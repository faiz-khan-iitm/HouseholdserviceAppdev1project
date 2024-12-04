import os
from werkzeug.security import generate_password_hash,check_password_hash
from flask import Flask,render_template,url_for, redirect,request,abort,flash,session
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

curr_dir=os.path.dirname(os.path.abspath(__file__))#

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///heaven.sqlite3'
app.config['SQLALCHEMY_TRACK_M0DIFICATIONS']=False
app.config['PASSWORD_HASH']='@faizkhan9090'
app.secret_key='heavydose7033'

app.config['UPLOAD_EXTENSIONS']=['.pdf']
app.config['UPLOAD_PATH']=os.path.join(curr_dir,'static',"pdfs")
db=SQLAlchemy()

db.init_app(app)
app.app_context().push()

#Models:-
class User(db.Model):
    __tablename__="user"
    id=db.Column(db.Integer,primary_key=True)
    user_name=db.Column(db.String(72),unique=True,nullable=False)
    password=db.Column(db.String(67),nullable=False)
    address=db.Column(db.String(67),nullable=True)
    pin_code=db.Column(db.Integer,nullable=True)
    is_admin=db.Column(db.Boolean,default=False)
    is_worker=db.Column(db.Boolean,default=False)
    is_customer=db.Column(db.Boolean,default=False)
    is_approved=db.Column(db.Boolean,default=False)
    rating_count=db.Column(db.Integer,default=0)
    mean_rating=db.Column(db.Float,default=0.0)
    worker_file=db.Column(db.String(100),nullable=True)
    worker_experience=db.Column(db.String(10),nullable=True)
    service_id=db.Column(db.Integer,db.ForeignKey('heavenServices.id',ondelete="SET NULL"),nullable=True)
    service=db.relationship('HeavenServices',back_populates="workers")
    worker_requests=db.relationship('HeavenRequest',back_populates="customer",foreign_keys="HeavenRequest.customer_id")
    customer_requests=db.relationship('HeavenRequest',back_populates="worker",foreign_keys="HeavenRequest.worker_id")


class HeavenServices(db.Model):
    __tablename__="heavenServices"
    id=db.Column(db.Integer,primary_key=True)
    service_name=db.Column(db.String(30),unique=True,nullable=False)
    service_description=db.Column(db.String(40),nullable=True)
    time_required=db.Column(db.String(30),nullable=True)
    base_price=db.Column(db.Integer,nullable=True)
    workers=db.relationship('User',back_populates="service",cascade="all, delete")
    request=db.relationship('HeavenRequest',back_populates="service",cascade="all, delete")


class HeavenRequest(db.Model):
    __tablename__="heavenRequest"
    id=db.Column(db.Integer,primary_key=True)
    service_id=db.Column(db.Integer,db.ForeignKey('heavenServices.id'),nullable=True)
    customer_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    worker_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=True)
    req_type=db.Column(db.String(20),nullable=False)
    description=db.Column(db.Text,nullable=True)
    status=db.Column(db.String(56),nullable=True)
    date_created=db.Column(db.Date,nullable=False, default=datetime.now().date())
    date_closed=db.Column(db.Date,nullable=True)
    rating_by_customer=db.Column(db.Float,default=0.0)
    review_by_customer=db.Column(db.String(20),nullable=True)
    service=db.relationship('HeavenServices',back_populates='request')
    customer=db.relationship('User',back_populates='customer_requests',foreign_keys=[customer_id])
    worker=db.relationship('User',back_populates='worker_requests',foreign_keys=[worker_id])

#Functions:-

def create_admin():
    with app.app_context():
        admin_user=User.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin_user=User(user_name="admin",password=generate_password_hash('7033655719'),is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created Succesfully")
with app.app_context():
    db.create_all()
    create_admin()

#Routes of pages
@app.route("/")
def home():
    return render_template('starter.html')


@app.route("/login_admin",methods=['GET','POST'])
def admin_login():
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        admin=User.query.filter_by(is_admin=True).first()
        if admin and check_password_hash(admin.password,password):
            session['username']=username
            session['is_admin']=True 
            flash("Logged in successfully",'success')
            return redirect("/admin_dashboard")
    return render_template('admin_login.html')

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        
        user=User.query.filter_by(user_name=username).first()
        if user and check_password_hash(user.password,password):
            session['user_id']=user.id
            session['is_customer']=user.is_customer
            session['is_worker']=user.is_worker 
            session['username']=user.user_name
            if user.is_customer:
                flash("Logged in successfull",'success')
                return redirect('/customer_dashboard')
            if user.is_worker:
                if user.is_approved==False:
                    flash('Please wait for admin approval','danger')
                    return redirect('/login')
                if user.service_id==None:
                    flash('Your service is not available now.Please create a new account with other service','danger')
                    return redirect('/login')
                return redirect('/worker_dashboard')
        flash("Login unsuccessfull. Please check username and password ",'danger')
    return render_template('login.html')

@app.route("/worker_register",methods=['GET','POST'])
def worker_register():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        address=request.form['address']
        worker_file=request.files['worker_file']
        worker_experience=request.form['worker_experience']
        pin_code=request.form['pin_code']
        service=request.form['service']
        service_id=HeavenServices.query.filter_by(service_name=service).first().id
        user=User.query.filter_by(user_name=username).first()
        if user:
            flash('User already exists . Please choose a different username','danger')
            return redirect('/worker_register')
        
        file_name=secure_filename(worker_file.filename)
        if file_name!="":
            file_exit=os.path.splitext(file_name)[1]
            renamed_file_name=username+file_exit
            if file_exit not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            worker_file.save(os.path.join(app.config['UPLOAD_PATH'],renamed_file_name))
       
        user=User(user_name=username,password=generate_password_hash(password),is_worker=True,address=address,pin_code=pin_code,worker_file=renamed_file_name,worker_experience=worker_experience,service_id=service_id)
        db.session.add(user)
        db.session.commit()
        flash('Registration successfull.Please login.','success')
        return redirect('/login')
    services=HeavenServices.query.all()
    return render_template('worker_register.html',services=services)

@app.route("/customer_register",methods=['GET','POST'])
def customer_register():
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        address=request.form['address']
        pin_code=request.form['pin_code']
        user=User.query.filter_by(user_name=username).first()
        if user:
            flash("User already exsist . Please choose a different name ",'danger')
            return redirect('/customer_register')
        user=User(user_name=username,password=generate_password_hash(password),is_customer=True,is_approved=True,address=address,pin_code=pin_code)
        db.session.add(user)
        db.session.commit()
        flash('Registration Successfull','success')
        return redirect('/login')
    return render_template('customer_register.html')

@app.route("/logout")
def logout():
    session.pop('username',None)
    session.pop('is_customer',None)
    session.pop('is_admin',None)
    session.pop('is_worker',None)
    flash('You have been logged out ','success')
    return redirect (url_for('login'))

@app.route("/admin_dashboard",methods=["GET","POST"])
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Please login first','danger')
        return redirect('/login')
    services=HeavenServices.query.all()
    requests=HeavenRequest.query.all()
    unapproved_workers=User.query.filter_by(is_approved=False,is_worker=True).all()
    return render_template('admin_dashboard.html',services=services,requests=requests,admin_name=session['username'],unapproved_workers=unapproved_workers)

@app.route("/admin_dashboard/create_service",methods=("GET","POST"))
def create_service():
    if not session.get('is_admin'):
        flash('Please login first','danger')
        return redirect('/login')
    
    if request.method=='POST':
        service_description=request.form['service_description']
        service_name=request.form['service_name']
        base_price=request.form['base_price']
        time_required=request.form['time_required']
        new_service=HeavenServices(service_description=service_description,service_name=service_name,base_price=base_price,time_required=time_required)
        db.session.add(new_service)
        db.session.commit()
        flash('Service created successfully','success')
        return redirect('/admin_dashboard')
    return render_template('create_service.html')

@app.route("/admin_dashboard/delete_service/<int:service_id>",methods=["POST","GET"])
def delete_service(service_id):
    if not session.get('is_admin'):
        flash('Please login first','danger')
        return redirect('/login')
    service=HeavenServices.query.get_or_404(service_id)
    approved_workers=User.query.filter_by(is_worker=True,is_approved=True,service_id=service_id).all()
    for worker in approved_workers:
        worker.is_approved=False 
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully','success')
    return redirect('/admin_dashboard')

@app.route("/admin_dashboard/edit_service/<int:service_id>", methods=["GET","POST"])
def edit_service(service_id):
    if not session.get('is_admin'):
        flash('Please login first','danger')
    service=HeavenServices.query.get_or_404(service_id)
    if request.method=="POST":
        service.service_name=request.form['service_name']
        service.service_description=request.form['service_description']
        service.base_price=request.form['base_price']
        service.time_required=request.form['time_required']
        db.session.commit()
        flash('service updated successfully','success')
        return redirect('/admin_dashboard')
    return render_template('edit_service.html',service=service)

@app.route("/admin_dashboard/view_worker/<int:worker_id>",methods=["GET","POST"])
def view_worker(worker_id):
    if not session.get('is_admin'):
        flash('please login first','danger')
        return redirect('/login')
    worker=User.query.get_or_404(worker_id)
    return render_template('view_worker.html',worker=worker)
                        
@app.route("/admin_dashboard/approve_worker/<int:worker_id>")   
def approve_worker(worker_id):
    if not session.get('is_admin'):
        flash('Please login first','danger')
        return redirect('/login')
    worker=User.query.get_or_404(worker_id)
    worker.is_approved=True
    db.session.commit()
    flash('Proffesional approved successfully','success')
    return redirect('/admin_dashboard')

@app.route("/admin_dashboard/reject_worker/<int:worker_id>")   
def reject_worker(worker_id):
    if not session.get('is_admin'):
        flash('Please login first','danger')
        return redirect('/login')
    worker=User.query.get_or_404(worker_id)
    pdf_file=worker.worker_file
    if pdf_file:
        path_file=os.path.join(app.config['UPLOAD_PATH'],pdf_file)
        if os.path.exists(pdf_file):
            try:
                os.remove(path_file)
                print('File deleted successfully')
            except Exception as e:
                print(f'Error deleting file:{e}')
        else:
            print('File not found')
    db.session.delete(worker)
    db.session.commit()
    flash('Proffesional rejected  successfully','success')
    return redirect('/admin_dashboard')
#Proffesional Dashboard

@app.route("/worker_dashboard",methods=["GET","POST"])
def worker_dashboard():
    if not session.get('is_worker'):
        flash('Please login first','danger')
        return redirect('/login')
    cid=User.query.filter_by(user_name=session['username']).first().id
    worker=User.query.filter_by(id=cid).first()
    if worker.is_approved==False:
        flash('Please wait for admin approval','danger')
        return redirect('/login')
        
    pending_requests=HeavenRequest.query.filter_by(worker_id=cid,status="pending" ,req_type='private').all()
    accepted_requests=HeavenRequest.query.filter_by(worker_id=cid,status="accepted").all()
    closed_requests=HeavenRequest.query.filter_by(worker_id=cid,status="closed").all()
    return render_template('worker_dashboard.html',pending_requests=pending_requests,
                           accepted_requests=accepted_requests,closed_requests=closed_requests)

@app.route("/customer_dashboard",methods=["GET","POST"])
def customer_dashboard():
    if not session.get('is_customer'):
        flash('Please login first')
        return redirect('/login')
    customer=User.query.filter_by(user_name=session["username"]).first()
    services=HeavenServices.query.join(User).filter(User.is_approved==True).all()#revisit here
    service_history=HeavenRequest.query.filter_by(customer_id=customer.id).filter(HeavenRequest.worker_id.is_not(None)).all()
    return render_template('customer_dashboard.html',services=services,service_history=service_history)

@app.route('/customer_dashboard/create_request/<int:service_id>',methods=["GET","POST"])
def create_request(service_id):
    if not session.get('is_customer'):
        flash('Please login first','danger')
        return redirect('/login')
    
    if request.method=="POST":
        worker=request.form.get('worker')
        description=request.form.get('description')
        cid=User.query.filter_by(user_name=worker).first().id
        customer=User.query.filter_by(user_name=session["username"]).first()
        

        service_request=HeavenRequest(customer_id=customer.id,
                                      worker_id=cid,service_id=service_id,description=description,status="pending",req_type="private")
        db.session.add(service_request)
        db.session.commit()
        flash("Request created successfully",'success')
        return redirect('/customer_dashboard')
    service=HeavenServices.query.get_or_404(service_id)
    workers=User.query.filter_by(is_worker=True,is_approved=True,service_id=service_id).all()
    return render_template('create_request.html',service=service,workers=workers)

@app.route('/customer_dashboard/edit_request/<int:service_request_id>',methods=["GET","POST"])
def edit_request(service_request_id):
    if not session.get('is_customer'):
        flash('Please login first','danger')
        return redirect('/login')
    service_request=HeavenRequest.query.get_or_404(service_request_id)
    if request.method=="POST":
        description=request.form.get('description')
        service_request.description=description
        db.session.commit()
        flash('Request updated successfully','success')
        return redirect('/customer_dashboard')
    return render_template('edit_request.html',service_request=service_request)

@app.route("/customer_dashboard/delete_request/<int:service_request_id>",methods=["GET","POST"])
def delete_request(service_request_id):
    if not session.get('is_customer'):
        flash('Please login first','danger')
        return redirect('/login')
    service_request=HeavenRequest.query.get_or_404(service_request_id)
    db.session.delete(service_request)
    db.session.commit()
    flash("Request updated successfully",'success')
    return redirect('/customer_dashboard')

@app.route("/customer_dashboard/search",methods=["GET","POST"])
def customer_search():
    if not session.get('is_customer'):
        flash('Please login first')
        return redirect('/login')
    search_type=request.args.get('search_type')
    search_query=request.args.get('search_query')
    services=[]

    if search_query:
        if search_type=="pin_code":
            services=HeavenServices.query.join(User).filter(User.is_approved==True,User.pin_code.like("%"+search_query+"%")).all()
        elif search_type=="service_name":
            services=HeavenServices.query.join(User).filter(HeavenServices.service_name.like("%"+search_query+"%")).all()
        elif search_type=="address":
            services=HeavenServices.query.join(User).filter(User.is_approved==True,User.address.like("%"+search_query+"%")).all()
    else:
            services=HeavenServices.query.join(User).filter(User.is_approved==True).all()

    return render_template('customer_search.html',services=services,customer_name=session['username'])

@app.route("/customer_dashboard/worker_profile/<int:worker_id>")
def worker_profile(worker_id):
    if not session.get('is_customer'):
        flash('Please login first','danger')
        return redirect('/login')
    new_worker=User.query.get(worker_id)
    reviews=HeavenRequest.query.filter_by(worker_id=worker_id,status="closed").all()
    return render_template("worker_profile.html",new_worker=new_worker, reviews=reviews, customer_name=session['username'])

@app.route("/worker_dashboard/accept_request/<int:request_id>",methods=["GET","POST"])
def accept_request(request_id):
    if not session.get('is_worker'):
        flash('Please login first','danger')
        return redirect('/login')
    service_request=HeavenRequest.query.get(request_id) #Query on the left is equivalent which is simply request id and we will 
    service_request.status="accepted"
    db.session.commit()
    flash("Request accepted successfully",'success')
    return redirect('/worker_dashboard')

@app.route("/worker_dashboard/reject_request/<int:request_id>",methods=["GET","POST"])
def reject_request(request_id):
    if not session.get('is_worker'):
        flash('Please login first','danger')
        return redirect('/login')
    service_request=HeavenRequest.query.get(request_id) #Query on the left is equivalent which is simply request id and we will 
    service_request.status="rejected"
    db.session.commit()
    flash("Request rejected successfully",'success')
    return redirect('/worker_dashboard')

@app.route("/customer_dashboard/close_request/<int:request_id>",methods=["GET","POST"])
def close_request(request_id):
    if not session.get('is_customer'):
        flash("Pleasse login first",'danger')
        return redirect("/login")
    service_request=HeavenRequest.query.get(request_id) #Query on the left is equivalent which is simply request id and we will 
    if not service_request:
        flash("Request not found",'danger')
        return redirect("/customer_dashboard")
    if request.method=="POST":
        review=request.form['review']
        rating=request.form['rating']

        service_request.status="closed"
        service_request.rating_by_customer=int(rating)
        service_request.review_by_customer=review
        service_request.date_closed=datetime.now().date()

        count_review_update=User.query.get(service_request.worker_id)
        temp=count_review_update.rating_count
        count_review_update.rating_count=count_review_update.rating_count + 1
        count_review_update.mean_rating=( count_review_update.mean_rating*temp + int(rating))/(count_review_update.rating_count)

        db.session.commit()
        flash("Request closed successfully",'success')
        return redirect("/customer_dashboard")

    worker=service_request.worker.user_name
    service=service_request.service.service_name
    return render_template("rating_reviews.html",worker=worker,service=service,request_id=request_id,customer_name=session['username'])

@app.route("/admin_dashboard/summary")
def admin_summary():
    if not session.get('is_admin'):
        flash("Please login first",'danger')
        return redirect('/rwu_login')
    customer_num=User.query.filter_by(is_customer=True).count()
    worker_num=User.query.filter_by(is_worker=True).count()

    accepted_num=HeavenRequest.query.filter_by(status="accepted").count()
    closesd_num=HeavenRequest.query.filter_by(status="closed").count()
    pending_num=HeavenRequest.query.filter_by(status="pending").count()
    rejected_num=HeavenRequest.query.filter_by(status="rejected").count()

    img_1=os.path.join(curr_dir,'static','img','img_1.png')
    img_2=os.path.join(curr_dir,'static','img','img_2.png')

    roles=['customers','Service Proffesional']
    num=[customer_num,worker_num]

    plt.figure(figsize=(6,4))
    sns.barplot(x=roles,y=num)
    plt.title('Numbers of user by role')
    plt.xlabel("User Role")
    plt.ylabel("Count")
    plt.savefig(img_1,format='png')

    status=['Accepted','Rejected','Closed','Pending']
    nums=[accepted_num,rejected_num,closesd_num,pending_num]
    colors=["#4CAF50","#F44366","#03A9F6","#FFC107"]

    plt.clf()
    plt.figure(figsize=(6,4))
    plt.pie(nums,labels=status,colors=colors,autopct='%1.1f%%')
    plt.title("Request Status Description")
    plt.savefig(img_2,format='png')

    return render_template('admin_summary.html',admin_name=session['username'],
                                                 customer_num=customer_num,
                                                  worker_num=worker_num,
                                                  accepted_num=accepted_num,
                                                  rejected_num=rejected_num,
                                                  pending_num=pending_num,
                                                  closesd_num=closesd_num)
@app.route("/admin_dashboard/search")
def admin_search():
    if not session.get('is_admin'):
        flash("please login first",'danger')
        return redirect("/rwu_login")
    search_type = request.args.get('search_type')
    search_query = request.args.get('search_query')

    if search_query:
        if search_type=="user":
            users=User.query.filter(User.user_name.like("%"+search_query+"%")).all()
            return render_template("admin_search.html",users=users,admin_name=session['username'])
        
        if search_type=="service":
            services=HeavenServices.query.filter(HeavenServices.service_name.like("%"+search_query+"%")).all()
            return render_template("admin_search.html",services=services,admin_name=session['username'])
    
    
    users=User.query.filter(User.is_approved==True).all()
    services=HeavenServices.query.all()

    return render_template("admin_search.html",services=services,users=users,admin_name=session['username'])

if __name__=="__main__":
    app.run(debug=True)
    
            

        














    
    
    
    
    
    
    
    