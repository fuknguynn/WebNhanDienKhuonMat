from flask import Flask, render_template
from pymongo import MongoClient
from datetime import datetime
import csv
import os

app = Flask(__name__)

# Cấu hình kết nối MongoDB
MONGO_URI = 'mongodb+srv://scjan123:vgbyostAaTl3Uttq@cluster0.aahzt.mongodb.net/'
DB_NAME = 'nhandienkhuonmat1'
COLLECTION_NAME = 'sukien'

# Kết nối đến MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
except Exception as e:
    print("Lỗi kết nối đến MongoDB:", e)

# Hàm lấy dữ liệu sinh viên từ MongoDB
def get_student_data():
    event_data = collection.find_one({"mask": "12DHTH13"})  # Thay ID sự kiện bằng giá trị thực
    if event_data and 'dssinhvien_thamgia' in event_data:
        return event_data['dssinhvien_thamgia']
    return []

# Hàm cập nhật trạng thái cho sinh viên trong MongoDB
def update_trangthai(student_data):
    for student in student_data:
        check_in_time = student.get('tgiancheck_in')
        check_out_time = student.get('tgiancheck_out')

        if check_in_time and check_out_time:
            student['trangthai'] = "Hoàn thành"
        elif not check_in_time and not check_out_time:
            student['trangthai'] = "Vắng"
        elif check_in_time:
            student['trangthai'] = "Chưa Check-out"
        else:
            student['trangthai'] = "Chưa Check-in"

    collection.update_one({"mask": "12DHTH13"}, {"$set": {"dssinhvien_thamgia": student_data}})

# Hàm xuất dữ liệu sang tệp CSV
def export_to_csv(student_data):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"thong_tin_diem_danh_{timestamp}.csv"  # Tên tệp CSV theo thời gian
    # Kiểm tra xem tệp đã tồn tại chưa, nếu có thì xóa tệp cũ
    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Ghi tiêu đề cột
        writer.writerow(['MSSV', 'Họ Tên', 'Lớp', 'Thời Gian Check-in', 'Thời Gian Check-out', 'Trạng Thái'])
        for student in student_data:
            writer.writerow([
                student.get('mssv', ''),
                student.get('hoten', ''),
                student.get('lop', ''),
                student.get('tgiancheck_in', 'Chưa check-in'),
                student.get('tgiancheck_out', 'Chưa check-out'),
                student.get('trangthai', 'Chưa xác định')
            ])

@app.route('/')
def index():
    student_data = get_student_data()
    update_trangthai(student_data)
    
    checked_in_students = [student for student in student_data if student.get('tgiancheck_in')]
    checked_out_students = [student for student in student_data if student.get('tgiancheck_out')]
    
    current_date = datetime.now().strftime('%d/%m/%Y')
    
    # Xuất dữ liệu ra tệp CSV
    export_to_csv(student_data)
    
    # Tìm sinh viên có thời gian check-in gần nhất
    latest_checked_in_student = None
    if checked_in_students:
        latest_checked_in_student = max(checked_in_students, key=lambda x: x.get('tgiancheck_in'))

    # Lấy tối đa 6 sinh viên gần nhất
    recent_students = sorted(checked_in_students, key=lambda x: x.get('tgiancheck_in'), reverse=True)[:6]

    # Truyền biến mssv vào template
    return render_template('index.html', 
                           student_data=latest_checked_in_student,
                           recent_students=recent_students,
                           checked_in=len(checked_in_students), 
                           checked_out=len(checked_out_students),
                           current_date=current_date,
                           mssv=latest_checked_in_student.get('mssv') if latest_checked_in_student else None)

if __name__ == '__main__':
    app.run(debug=True)