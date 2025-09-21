from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
import models.data_manager as dm

# ฟังก์ชันหลักสำหรับสร้างเส้นทาง (Route) ทั้งหมดในแอป
def init_routes(app):

    # สร้าง Decorator ชื่อ admin_required เพื่อตรวจสอบสิทธิ์แอดมิน
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # ถ้าใน session ไม่ได้บอกว่าเป็นแอดมิน
            if not session.get('is_admin'):
                # ให้แสดงข้อความแจ้งเตือน แล้วเด้งกลับไปหน้าแรก
                flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function

    # สร้าง Decorator ชื่อ login_required เพื่อตรวจสอบว่าล็อคอินหรือยัง
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # ถ้าใน session ไม่มี user_id (ยังไม่ได้ล็อคอิน)
            if 'user_id' not in session:
                # ให้แสดงข้อความแจ้งเตือน แล้วส่งไปหน้าล็อคอิน
                flash('กรุณาล็อคอินเพื่อดำเนินการต่อ', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    # Route สำหรับหน้าแรกของเว็บ ('/')
    @app.route('/')
    def home():
        # เช็คว่าเป็นแอดมินหรือไม่ เพื่อเลือกว่าจะแสดงหน้าไหน
        if session.get('is_admin'):
            # ถ้าเป็นแอดมิน: แสดงหน้ารายชื่อผู้สมัครทั้งหมด
            all_candidates = dm.get_all_candidates()
            # จัดเรียงรายชื่อตามชื่อจริง
            sorted_candidates = sorted(all_candidates, key=lambda c: c['first_name'])
            return render_template('admin/all_candidates.html', candidates=sorted_candidates)
        else:
            # ถ้าเป็นผู้ใช้ทั่วไป: แสดงหน้าตำแหน่งงานที่กำลังเปิดรับสมัคร
            # รับค่า 'sort_by' จาก URL เพื่อใช้จัดเรียง ถ้าไม่มีให้ใช้ 'title' เป็นค่าเริ่มต้น
            sort_by = request.args.get('sort_by', 'title')
            
            jobs = dm.get_open_jobs_with_details()
            
            # ส่วนของการจัดเรียงข้อมูลตามค่าที่ได้รับมา
            if sort_by == 'company':
                jobs.sort(key=lambda j: j['company_name'])
            elif sort_by == 'deadline':
                jobs.sort(key=lambda j: j['deadline'])
            else: # ถ้าไม่ตรงกับเงื่อนไขไหนเลย ให้เรียงตามชื่อตำแหน่งงาน
                jobs.sort(key=lambda j: j['title'])
                
            return render_template('candidate/open_jobs.html', jobs=jobs)

    # Route สำหรับหน้าล็อคอิน รับทั้งแบบ GET (เปิดหน้าเว็บ) และ POST (กดปุ่มส่งข้อมูล)
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # เมื่อผู้ใช้กรอกข้อมูลแล้วกดปุ่ม Login (ส่งมาแบบ POST)
        if request.method == 'POST':
            email = request.form['email']
            user = dm.find_user_by_email(email)
            # ถ้าเจอผู้ใช้ในระบบ
            if user:
                # เก็บข้อมูลที่จำเป็นลงใน session
                session['user_id'] = user['candidate_id']
                session['user_email'] = user['email']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                session['is_admin'] = user['is_admin']
                flash(f"ยินดีต้อนรับคุณ {session['user_name']}!", 'success')
                # ส่งกลับไปที่หน้าแรก
                return redirect(url_for('home'))
            else:
                # ถ้าไม่เจอผู้ใช้ในระบบ ก็แจ้งเตือน
                flash('อีเมลไม่ถูกต้อง กรุณาลองอีกครั้ง', 'danger')
        # ถ้าเป็นการเปิดหน้าเว็บเฉยๆ (แบบ GET) ก็ให้แสดงหน้า login.html
        return render_template('shared/login.html')

    # Route สำหรับการล็อคเอาท์
    @app.route('/logout')
    def logout():
        # เคลียร์ข้อมูลทั้งหมดใน session
        session.clear()
        flash('คุณได้ออกจากระบบแล้ว', 'info')
        # ส่งกลับไปที่หน้าล็อคอิน
        return redirect(url_for('login'))
        
    # Route สำหรับดูรายละเอียดผู้สมัครแต่ละคน (แอดมินดูได้อย่างเดียว)
    @app.route('/candidate/<candidate_id>')
    @admin_required
    def candidate_detail(candidate_id):
        # ดึงข้อมูลผู้สมัครจาก id ที่ได้รับมา
        candidate = dm.find_candidate_by_id(candidate_id)
        # ถ้าหาผู้สมัครไม่เจอ ให้แจ้งเตือนแล้วกลับหน้าแรก
        if not candidate:
            flash('ไม่พบข้อมูลผู้สมัคร', 'danger')
            return redirect(url_for('home'))
        
        # ดึงข้อมูลใบสมัครงานทั้งหมดของผู้สมัครคนนี้
        applications = dm.get_applications_for_candidate(candidate_id)
        
        # จัดเรียงใบสมัคร
        sort_by = request.args.get('sort_by', 'job_title')
        if sort_by == 'company_name':
            applications.sort(key=lambda a: a['company_name'])
        elif sort_by == 'application_date':
            applications.sort(key=lambda a: a['application_date'], reverse=True)
        else:
            applications.sort(key=lambda a: a['job_title'])
            
        return render_template('admin/candidate_detail.html', candidate=candidate, applications=applications)

    # Route สำหรับการกดสมัครงาน (ต้องล็อคอินก่อน)
    @app.route('/apply/<job_id>', methods=['POST'])
    @login_required
    def apply(job_id):
        # แอดมินไม่สามารถสมัครงานได้
        if session.get('is_admin'):
             flash('แอดมินไม่สามารถสมัครงานได้', 'warning')
             return redirect(url_for('home'))

        # ดึง id ของผู้ใช้ที่ล็อคอินอยู่จาก session
        candidate_id = session['user_id']
        # เรียกใช้ฟังก์ชัน add_application เพื่อเพิ่มข้อมูลใบสมัคร
        result = dm.add_application(job_id, candidate_id)
        
        # แสดงข้อความแจ้งเตือนตามผลลัพธ์ที่ได้กลับมา
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'danger')
            
        # กฎของระบบ: เมื่อสมัครเสร็จ ต้องกลับไปหน้าแรก (หน้ารวมตำแหน่งงาน)
        return redirect(url_for('home'))
    
    # Route สำหรับหน้ารายละเอียดของงานแต่ละชิ้น (ต้องล็อคอินก่อน)
    @app.route('/job/<job_id>')
    @login_required 
    def job_detail(job_id):
        # ดึงข้อมูลของงานจาก id
        job = dm.get_job_details_by_id(job_id)
        # ถ้าหางานไม่เจอ ให้แจ้งเตือนแล้วกลับหน้าแรก
        if not job:
            flash('ไม่พบข้อมูลตำแหน่งงาน', 'danger')
            return redirect(url_for('home'))

        # เช็คว่าผู้ใช้คนนี้เคยสมัครงานนี้ไปแล้วหรือยัง
        already_applied = False
        if session.get('user_id'):
            candidate_id = session['user_id']
            already_applied = dm.has_candidate_applied(candidate_id, job_id)

        # ส่งข้อมูลทั้งหมดไปแสดงผลที่หน้า job_detail.html
        return render_template('candidate/job_detail.html', job=job, already_applied=already_applied)
    
    # Route สำหรับหน้าแสดงทุกตำแหน่งงาน (สำหรับแอดมินเท่านั้น)
    @app.route('/admin/jobs')
    @admin_required
    def admin_all_jobs():
        sort_by = request.args.get('sort_by', 'title')
        
        # ดึงข้อมูลงานทั้งหมด (ทั้งที่เปิดและปิด) พร้อมจำนวนผู้สมัคร
        jobs = dm.get_all_jobs_with_details()
        
        # ส่วนของการจัดเรียงข้อมูล
        if sort_by == 'company':
            jobs.sort(key=lambda j: j['company_name'])
        elif sort_by == 'applicants':
            # ต้องแปลงจำนวนผู้สมัครเป็นตัวเลข (int) ก่อน ถึงจะเรียงลำดับถูก
            jobs.sort(key=lambda j: int(j['applicant_count']), reverse=True)
        else: # Default to title
            jobs.sort(key=lambda j: j['title'])
            
        return render_template('admin/all_jobs.html', jobs=jobs)