# How to run my own scraper?

1. You need python installed on your computer  
2. Clone this repository into your machine  
3. Install the required libraries specified in the requirements.txt file
4. Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on your computer    
5. Open your **terminal** (MacOS, Linux) or **cmd** (Windows), navigate to the project folder and run:  
if you are using pipenv: `pipenv run python app.py` 
if not: `python app.py`
6. You will need a .db specifying city_name and beach_name for each beach  
WARNING:  
7.Keep in mind this scraper gets accurate results only around 85% of the times so you might want to check your results later, search for meaningless beach names or crazy 
coordinates
