from flask import Flask, request, render_template
from ultralytics import YOLO
from merged_mrz_FINAL import *
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'photo' not in request.files:
        return 'No file part'
    file = request.files['photo']
    if file.filename == '':
        return 'No selected file'
    if file:
        file_path = 'files/' + file.filename  # Путь к сохраненному файлу
        file.save(file_path)  # Сохранение файла на сервере
        match,country_code,message = main2(file_path)  # Передача пути к файлу в функцию main()
        if match:
            if country_code == 'SRB':
                model = YOLO('runs/clasify/best_srb/weights/6epoch.pt')
                results = model.predict(file_path)
                if results[0].probs.top1 == 0:
                    message = "This passport is legal"
                elif results[0].probs.top1 == 1:
                    message = "This passport is fake by background"
                else:
                    message = "This passport is fake by misspeling"

            elif country_code == 'AZE' :
                model = YOLO('runs/clasify/train9/weights/best.pt')
                results = model.predict(file_path)
                if results[0].probs.top1 == 0:
                    message = "This passport is legal"
                elif results[0].probs.top1 == 1:
                    message = "This passport is fake by background"
                else:
                    message = "This passport is fake by misspeling"
        return render_template('index.html', message=message)


if __name__ == '__main__':
    app.run(debug=True)
