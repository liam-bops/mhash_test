from flask import Flask, Response, render_template, request, jsonify
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import numpy as np
import pickle
import psycopg2
import cv2 as cv
import scraping 
import weather
import requests
import geocoder
conn = psycopg2.connect(
     host="db.eoehrierllfhmxlltdyf.supabase.co",
     database="postgres",
     user="postgres",
     password="Mhash@win576"
 )

# # Create a cursor object
cur = conn.cursor()

# # Execute a query
# cur.execute("SELECT * FROM your_table")

# # Fetch the results
# results = cur.fetchall()

# # Close the cursor and connection
# cur.close()
# conn.close()
import json
g = geocoder.ip('me')
#print(f"City: {g.city}, State: {g.state}, Latitude: {g.lat}, Longitude: {g.lng}")
city = g.city
#print(city)
URL = f"http://api.weatherapi.com/v1/current.json?key=67859d3bc72046bcb9783007231710&q={city}&aqi=no&days=7"
a = requests.get(URL)
data = a.json()
#print(data)
data = data['current']
"""print(data['temp_c'])
print(data['condition']['text'])
#print(data['condition']['icon'])    
print(data['wind_kph'])
print(data['humidity'])
print(data['pressure_mb'])
print(data['precip_mm'])
print(data['cloud'])
print(data['feelslike_c'])"""
weather1 = dict()
weather1['current temperature'] = data['temp_c']
weather1['current condition'] = data['condition']['text']
weather1['current wind in kmph'] = data['wind_kph']
weather1['current humidity'] = data['humidity']
weather1['current pressure in mb'] = data['pressure_mb']
weather1['current precipitation in mm'] = data['precip_mm']


json_str = json.dumps(weather1)
print(json_str)
update_query = f"UPDATE farmersindian SET currentweather =  %s"

    # Execute the query for all rows in the table
cur.execute(update_query,(json_str,))

    # Commit the changes
conn.commit()


app = Flask(__name__)
OUTPUT_FOLDER = 'static'
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
crop_names = ['potato','tomato','bellpepper']
potato_classes = ['Early Blight','Late Blight','Healthy']
tomato_classes = ['Bacterial spot', 'Early blight','Late blight','Leaf Mold', 'Septoria leaf spot','Spider mites Two spotted spider mite','Target Spot', 'Yellow Leaf Curl Virus','Mosaic virus','Healthy']
bellpepper_classes = ['Bacterial spot', 'Healthy']

def predict(crop,data):
    # data = data.numpy()
    classes = []
    model = None
    data = np.expand_dims(data,axis=0)
    print(data.shape)
    # print(crop)
    # print(crop == 'potato')
    if crop == 'Potato':
        classes = potato_classes
        model = pickle.load(open(r'potato.pkl', 'rb'))
    elif crop == 'Tomato':
        classes = tomato_classes
        model = pickle.load(open(r'tomato.pkl', 'rb'))
    elif crop == 'Bell pepper':    
        classes = bellpepper_classes
        model = pickle.load(open(r'bellpepper.pkl', 'rb'))
    prediction = model.predict(data)
    print(prediction)
    return classes[np.argmax(prediction)]



conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="Mhash@win576",
    host="db.eoehrierllfhmxlltdyf.supabase.co",
    port="5432"
)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = conn.cursor()
        cur.execute("SELECT * FROM farmersindian WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        if user:
            with open("username.txt", "w") as username_file:
                username_file.write(username)
            with open("password.txt", "w") as pass_file:
                pass_file.write(password)    
            return render_template('index.html',weather = weather.get_weather())
        else:
            return render_template('invalidlogin.html')
    return render_template('login.html')

@app.route('/index.html')
def index():
    return render_template('index.html', weather = weather.get_weather())

@app.route('/chatbot.html')
def chatbot():
    return render_template('streamlit_template.html')

@app.route('/helpline')
@app.route('/helpline.html')
def helpline():
    return render_template('helpline.html', nameList = scraping.nameList, urlList = scraping.urlList, list1 = scraping.list1)

@app.route('/disease.html',methods=['GET','POST'])
@app.route('/diseasedetection',methods=['GET','POST'])
def disease():
    if request.method == 'POST':
        crop = request.form['crop']
        image = request.files.get('imagefile').read()
        image = cv.imdecode(np.frombuffer(image, np.uint8), cv.IMREAD_COLOR)
        image = cv.resize(image,(256,256))
        cv.imwrite('static/currentimage.png',image)
        # cv.imshow('image',image)
        # cv.waitKey(0)
        print(crop)
        prediction = predict(crop,image)
        print("PREDICTION : ", prediction)
        return render_template('disease.html',prediction=prediction,crop = crop,url="static/currentimage.png")
    if request.method == 'GET':
        return render_template('disease.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = conn.cursor()
        cur.execute("INSERT INTO farmersindian (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cur.close()
        return render_template('registersucess.html')
    return render_template('register.html')



@app.route('/community')
@app.route('/forum.html')
def community():
    return render_template('rocketchatembed.html')

def generate_frames():
    camera = cv.VideoCapture(0)
    while True:
        # Capture frame-by-frame from the camera.
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode the frame in JPEG format.
            # frame = cv.resize(frame, (640,480))
            ret, buffer = cv.imencode('.jpg', frame)
            
            frame = buffer.tobytes()
            # cv.imshow("lmao", frame)

        # Yield the frame in byte format.
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
    camera.close()

@app.route('/vidfeed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/livestream.html')
def video_feed_page():
    return render_template('livestream.html')


if __name__ == '__main__':
    app.run(debug=True)
 