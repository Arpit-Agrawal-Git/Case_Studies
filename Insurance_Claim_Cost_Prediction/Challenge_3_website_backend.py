import re
import nltk
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer

# Download stopwords
nltk.download('stopwords')
nltk.download('punkt')

stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = re.sub(r'\W', ' ', text)  # Remove non-word characters
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    text = text.lower()  # Convert to lower case
    return text

def extract_keywords(description):
    words = word_tokenize(description)
    words = [word for word in words if word not in stop_words]
    return words

body_parts = ['head', 'eye', 'arm', 'leg', 'back', 'hand', 'foot', 'shoulder']
injury_causes = ['fall', 'slip', 'trip', 'cut', 'burn', 'strain', 'sprain', 'hit']

def categorize_keywords(keywords, categories):
    for word in keywords:
        for category in categories:
            if category in word:
                return category
    return 'other'

# Load the pre-trained model
model = joblib.load('best_xgboost_model.joblib')

# Load the label encoder
label_encoder = joblib.load('label_encoders.joblib')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

    
@app.route('/process', methods=['POST'])
def process_data():
    try:
        data = request.get_json()

        print("Received data:", data)

        # Convert incoming JSON data to DataFrame
        data_df = pd.DataFrame([data])

        print(data_df.info())

        # Apply cleaning and keyword extraction
        data_df['Cleaned Description'] = data_df['Cause Description'].apply(lambda x: clean_text(str(x)))
        data_df['Keywords'] = data_df['Cleaned Description'].apply(lambda x: extract_keywords(x))
        # print(data_df['Keywords'])

        # Extract Body Part and Injury Cause
        data_df['Body Part'] = data_df['Keywords'].apply(lambda x: categorize_keywords(x, body_parts))
        # print(data_df['Body Part'])
        data_df['Injury Cause'] = data_df['Keywords'].apply(lambda x: categorize_keywords(x, injury_causes))
        # print(data_df['Injury Cause'])
        # Encode categorical features
        features = ['Accident State', 'Sector/Industry', 'Loss Type', 'Litigation', 'Occupation', 'Body Part', 'Injury Cause']
        for col in features:
            # print(data_df[col].dtype)
            if data_df[col].dtype == 'object':
                le = label_encoder[col]
                data_df[col] = le.transform(data_df[col].astype(str))
                # print(data_df[col])
        # Prepare the data for prediction
        X = data_df[features]

        print(X)

        # Make predictions
        predictions = model.predict(X)

        # Prepare the response
        data_df['Predicted Claim Cost'] = predictions
        processed_data = data_df[['Accident State', 'Sector/Industry', 'Loss Type', 'Litigation', 'Occupation', 'Body Part', 'Injury Cause', 'Predicted Claim Cost']].to_dict(orient='records')

        print("Processed data:", processed_data)
        return jsonify(processed_data)
    except Exception as e:
        print("Error occurred:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

