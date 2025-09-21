import csv
from datetime import datetime
import re

DATA_PATH = './data/'

# อ่านไฟล์ csv
def read_csv(filename):
    data = []
    with open(DATA_PATH + filename, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            data.append(row)
    return data

def write_csv(filename, data, fieldnames):

    with open(DATA_PATH + filename, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# ตรวจเช็คความถูกต้องของ email
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

# จัดการ Data

# รับข้อมูลบริษัท
def get_all_companies():
    return read_csv('companies.csv')

# รับข้อมูลงาน
def get_all_jobs():
    return read_csv('jobs.csv')

# รับข้อมูล candidate
def get_all_candidates():
    candidates = read_csv('candidates.csv')
    # กรอง admin
    return [c for c in candidates if c['is_admin'].lower() != 'true']

# รับข้อมูลการสมัคร
def get_all_applications():
    return read_csv('applications.csv')

# Authen หา user กับ admin
def find_user_by_email(email):
    if not is_valid_email(email):
        return None
    all_users = read_csv('candidates.csv')
    for user in all_users:
        if user['email'] == email:
            # Convert 'is_admin' to boolean
            user['is_admin'] = user['is_admin'].lower() == 'true'
            return user
    return None

# ดึงค่า candidate จาก id (query ดู detail)
def find_candidate_by_id(candidate_id):
    for candidate in read_csv('candidates.csv'):
        if candidate['candidate_id'] == candidate_id:
            return candidate
    return None

# ดึง job จาก id (query ดู detail)
def find_job_by_id(job_id):
    for job in get_all_jobs():
        if job['job_id'] == job_id:
            return job
    return None

# ดึง detail งานออกมา เช่น การดึงจำนวนของผู้สมัคร
def get_open_jobs_with_details():

    jobs = get_all_jobs()
    companies = {c['company_id']: c for c in get_all_companies()}
    applications = get_all_applications()
    
    applicant_counts = {}
    for app in applications:
        applicant_counts[app['job_id']] = applicant_counts.get(app['job_id'], 0) + 1

    open_jobs = []
    for job in jobs:
        if job['status'] == 'open':
            job['company_name'] = companies.get(job['company_id'], {}).get('name', 'N/A')
            job['applicant_count'] = applicant_counts.get(job['job_id'], 0)
            open_jobs.append(job)
    return open_jobs


def get_applications_for_candidate(candidate_id):
    applications = get_all_applications()
    jobs = {j['job_id']: j for j in get_all_jobs()}
    companies = {c['company_id']: c for c in get_all_companies()}
    
    candidate_apps = []
    for app in applications:
        if app['candidate_id'] == candidate_id:
            job_details = jobs.get(app['job_id'])
            if job_details:
                company = companies.get(job_details['company_id'])
                candidate_apps.append({
                    'job_title': job_details.get('title', 'N/A'),
                    'company_name': company.get('name', 'N/A') if company else 'N/A',
                    'application_date': app['application_date']
                })
    return candidate_apps

# ฟังก์ชันสมัครงาน
def add_application(job_id, candidate_id):
    job = find_job_by_id(job_id)
    if not job:
        return {'success': False, 'message': 'Job not found.'}

    # Business Rule: Check deadline
    deadline = datetime.strptime(job['deadline'], '%Y-%m-%d').date()
    today = datetime.now().date()
    if today > deadline:
        return {'success': False, 'message': 'The application deadline has passed.'}

    # Business Rule: ใช้ฟังก์ชันเพื่อเช็คว่าเคยสมัครไปแล้วหรือยัง
    if has_candidate_applied(candidate_id, job_id):
        return {'success': False, 'message': 'You have already applied for this job.'}
    
    # Add new application
    applications = get_all_applications()
    new_app = {
        'job_id': job_id,
        'candidate_id': candidate_id,
        'application_date': today.strftime('%Y-%m-%d')
    }
    applications.append(new_app)
    write_csv('applications.csv', applications, fieldnames=['job_id', 'candidate_id', 'application_date'])
    
    return {'success': True, 'message': 'Application submitted successfully!'}

# ดึง detail งานออกมาที่เอาไป join กับ company เอาไว้ดูรายละเอียด
def get_job_details_by_id(job_id):

    job = find_job_by_id(job_id)
    if not job:
        return None
    
    # ดึงข้อมูลบริษัททั้งหมดมาเก็บใน dictionary เพื่อให้ง่ายต่อการค้นหา
    companies = {c['company_id']: c for c in get_all_companies()}
    company_info = companies.get(job['company_id'], {})

    # เพิ่มชื่อบริษัทและสถานที่ตั้งเข้าไปใน object ของ job
    job['company_name'] = company_info.get('name', 'N/A')
    job['location'] = company_info.get('location', 'N/A') 
    
    return job

# ตรวจสอบว่าเคยสมัครไปหรือยัง
def has_candidate_applied(candidate_id, job_id):
    
    applications = get_all_applications()
    for app in applications:
        if app['candidate_id'] == str(candidate_id) and app['job_id'] == str(job_id):
            return True
    return False

def get_all_jobs_with_details():
    
    jobs = get_all_jobs()
    companies = {c['company_id']: c for c in get_all_companies()}
    applications = get_all_applications()
    
    applicant_counts = {}
    for app in applications:
        applicant_counts[app['job_id']] = applicant_counts.get(app['job_id'], 0) + 1

    all_jobs_details = []
    for job in jobs:
        job['company_name'] = companies.get(job['company_id'], {}).get('name', 'N/A')
        job['applicant_count'] = applicant_counts.get(job['job_id'], 0)
        all_jobs_details.append(job)
        
    return all_jobs_details