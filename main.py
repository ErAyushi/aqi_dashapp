from flask import Flask, render_template, request
import pandas as pd
import pickle
import psycopg2
import folium
from folium.plugins import MarkerCluster

app = Flask(__name__, static_folder='templates')

# Connect to PostgreSQL database
conn = psycopg2.connect(
    host="192.168.20.97",
    database="postgres",
    user="postgres",
    password="master@123"
)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    # Get user input values
    month = int(request.form['month'])
    year = int(request.form['year'])
    date = pd.to_datetime('{}-{}-01'.format(year, month))

    # Check if the data exists in the database
    cursor = conn.cursor()
    cursor.execute(f"SELECT aqi FROM eda WHERE date = '{date}'")
    result = cursor.fetchone()
    if result:
        # AQI value exists in the database, retrieve and show it
        aqi = result[0]
    else:
        # AQI value doesn't exist in the database, use the model to make a prediction
        with open('xg2.pickle', 'rb') as f:
            xg = pickle.load(f)

        data = pd.read_csv("eda_lat_lon.csv")
        # Create a dictionary to store the predictions and coordinates for all cities
        predictions = {}

        # Iterate over all city-encoded values
        for city_encoded in range(1, 27):
            # Create a user input dataframe for the current city
            user_input = pd.DataFrame({
                'pm2.5': [0],
                'pm10': [0],
                'no': [0],
                'no2': [0],
                'nox': [0],
                'nh3': [0],
                'co': [0],
                'so2': [0],
                'o3': [0],
                'benzene': [0],
                'toluene': [0],
                'month': [month],
                'year': [year],
                'city_encoded': [city_encoded]
            })

            # Calculate the mean values for the other features for the specified city and month
            city_month_data = data[(data['city_encoded'] == city_encoded) & (data['month'] == month)]
            mean_pm2_5 = city_month_data['pm2.5'].mean()
            mean_pm10 = city_month_data['pm10'].mean()
            mean_no = city_month_data['no'].mean()
            mean_no2 = city_month_data['no2'].mean()
            mean_nox = city_month_data['nox'].mean()
            mean_nh3 = city_month_data['nh3'].mean()
            mean_co = city_month_data['co'].mean()
            mean_so2 = city_month_data['so2'].mean()
            mean_o3 = city_month_data['o3'].mean()
            mean_benzene = city_month_data['benzene'].mean()
            mean_toluene = city_month_data['toluene'].mean()

            # Update the user input dataframe with the mean values for the other features
            user_input['pm2.5'] = mean_pm2_5
            user_input['pm10'] = mean_pm10
            user_input['no'] = mean_no
            user_input['no2'] = mean_no2
            user_input['nox'] = mean_nox
            user_input['nh3'] = mean_nh3
            user_input['co'] = mean_co
            user_input['so2'] = mean_so2
            user_input['o3'] = mean_o3
            user_input['benzene'] = mean_benzene
            user_input['toluene'] = mean_toluene

            # Use the model to make a prediction for the current city and add it to the dictionary
            prediction = xg.predict(user_input)[0]
            predictions[city_encoded] = (
            prediction, city_month_data.iloc[0]['lat'], city_month_data.iloc[0]['lon'])

            # Save the predicted values to the database
        cursor.execute(
            f"INSERT INTO eda VALUES ('{date}', {predictions[1][0]}, {predictions[2][0]}, {predictions[3][0]}, {predictions[4][0]}, {predictions[5][0]}, {predictions[6][0]}, {predictions[7][0]}, {predictions[8][0]}, {predictions[9][0]}, {predictions[10][0]}, {predictions[11][0]}, {predictions[12][0]}, {predictions[13][0]}, {predictions[14][0]}, {predictions[15][0]}, {predictions[16][0]}, {predictions[17][0]}, {predictions[18][0]}, {predictions[19][0]}, {predictions[20][0]}, {predictions[21][0]}, {predictions[22][0]}, {predictions[23][0]}, {predictions[24][0]}, {predictions[25][0]}, {predictions[26][0]})")
        conn.commit()

        # Use Folium to create a map with markers for each city and its predicted AQI value
        map = folium.Map(location=[20.5937, 78.9629], zoom_start=4)
        marker_cluster = MarkerCluster().add_to(map)

        for city_encoded in predictions:
            prediction, lat, lon = predictions[city_encoded]
            city = data[data['city_encoded'] == city_encoded].iloc[0]['city']
            folium.Marker(location=[lat, lon], popup=f"{city}: {prediction}").add_to(marker_cluster)


        map.save('templates/map.html')

        # Set AQI value to the prediction for the user's city
        user_city = data[data['city_encoded'] == int(request.form['city_encoded'])].iloc[0]['city']
        aqi = predictions[int(request.form['city_encoded'])][0]
        message = f"The predicted AQI for {user_city} in {date.strftime('%B %Y')} is {aqi}."

    return render_template('result.html', message=message)
if __name__ == '__main__':
    app.run(debug=True,port=5020)

