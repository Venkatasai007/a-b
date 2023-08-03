from flask import Flask,render_template,request,url_for,session,redirect
from pymysql import connections
import boto3
from config import *

app=Flask(__name__)
app.secret_key = 'AP21110011'

db_conn=connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)

S3 = boto3.resource('s3',
                    region_name='us-east-1',
                    aws_access_key_id="AKIA563MT4VMQG5EGW5R",
                    aws_secret_access_key="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")


@app.route("/",methods=['GET','POST'])
def home():
    return  render_template("home.html")
    


@app.route("/admin_login")
def admin_login():
    return  render_template("admin_login.html")

@app.route("/admin_page",methods=['GET','POST'])
def admin_page():
    if request.method=='POST':
        user_name=request.form.get('username')
        passw=request.form.get('pass')
        if(user_name==admin_name and passw==admin_pass):
            user_info = {
                'User': user_name,
                'Password': passw
            }
            session['user_info'] = user_info
            return redirect('/protected')
    return  render_template("admin_login.html")

@app.route("/protected")
def protected():
    try:
        user_info = session.get('user_info')
        if user_info:
            return render_template("admin_page.html")
        else:
            return "Access denied."
    except Exception as e:
        return str(e)

@app.route("/update_pass")
def update_pass():
    try:
        user_info = session.get('user_info')
        if user_info:
            return render_template("update_password.html")
        else:
            return "Access denied."
    except Exception as e:
        return str(e)
    

@app.route("/updatePassPage",methods=['GET','POST'])
def new_password():
    try:
        user_info = session.get('user_info')
        if user_info:
            Roll=request.form.get('Roll')
            passw=request.form.get('pass')
            new_passw=request.form.get('new_pass')
            if(passw==new_passw):
                cursor=db_conn.cursor()
                query = "UPDATE data SET password = %s WHERE Roll = %s"
                cursor.execute(query, (passw, Roll))
                db_conn.commit()
                return f"Updated the password of {Roll}"
            else:
                return "Access denied."
    except Exception as e:
        return str(e)
    
        

    
@app.route("/addstudent")
def addstudent():
    try:
        user_info = session.get('user_info')
        if user_info:
            return  render_template("addstudent.html")
        else:
            return "Access denied."
    except Exception as e:
        return str(e)
    

@app.route("/student_register")
def student_register():
    try:
        user_info = session.get('user_info')
        if user_info:
            return  render_template("addstudent.html")
        else:
            return f"access denied"
    except Exception as e:
        return str(e)

@app.route("/admin_logout")
def admin_logout():
    session.pop('user_info', None)
    return  render_template("admin_login.html")

@app.route("/student_login")
def student_login():
    return  render_template("student_login.html")


@app.route("/change_pass")
def change_pass():
    return  render_template("change_pass.html")

@app.route("/changing_pass",methods=['GET','POST'])
def changing_pass():
    try:
        Roll=request.form.get('Roll')
        curr_pass=request.form.get('current_pass')
        passw=request.form.get('pass')
        new_passw=request.form.get('new_pass')
        query = "SELECT password FROM data WHERE Roll = %s"
        cursor=db_conn.cursor()
        cursor.execute(query, (Roll))
        original_pass = cursor.fetchone()
        if curr_pass==original_pass[0]:
            if(passw==new_passw):
                query = "UPDATE data SET password = %s WHERE Roll = %s"
                cursor.execute(query, (passw, Roll))
                db_conn.commit()
        return render_template("student_login.html")
    except Exception as e:
        return str(e)
    
        
    



@app.route("/student_page",methods=['GET','POST'])
def student_page():
    try:
        if request.method=='POST':
            student_user_name=request.form.get('username')
            passw=request.form.get('pass')
            cursor=db_conn.cursor()
            query = "SELECT Roll FROM data WHERE Roll = %s"
            cursor.execute(query, (student_user_name,))
            result = cursor.fetchone()
            if result:
                query = "SELECT password FROM data WHERE Roll = %s"
                cursor.execute(query, (student_user_name))
                original_pass = cursor.fetchone()[0]
                if passw==original_pass:
                    user = {
                    'User': student_user_name,
                    'Password': passw
                    }
                    session['user'] = user
                    return redirect('/protected_student')
    except Exception as e:
        return str(e)
    return  render_template("student_login.html")


@app.route("/protected_student")
def protected_student():
    try:
        user = session.get('user')
        if user:
            cursor=db_conn.cursor()
            query = "SELECT * FROM data WHERE Roll = %s"
            cursor.execute(query, (user['User']))
            result = cursor.fetchone()
            return render_template("student_page.html",name=result[0],gname=result[1],dob=result[2],roll=result[3],image_url=result[4])
        else:
            return "Access denied."
    except Exception as e:
        return str(e)


@app.route("/student_logout")
def student_logout():
    session.pop('user', None)
    return  render_template("home.html")




@app.route("/add",methods=['GET','POST'])
def displayaddemp():
    try:
        user_info = session.get('user_info')
        if user_info:
            name=request.form.get('name')
            gname=request.form.get('G-name')
            dob=request.form.get('dob')
            # password=hash_password(dob)
            password =str(dob)
            file = request.files['img_file']
            insert_sql="INSERT INTO data VALUES (NULL,%s,%s,%s,%s,%s)"
            cursor=db_conn.cursor()
            try:
                # studentdb - database name
                #data - table
                if file:
                    filename = file.filename
                #    S3.upload_fileobj(file, 'mybucket-294', filename)
                    s3_bucket = S3.Bucket('my-student')
                    s3_object = s3_bucket.Object(filename)
                    s3_object.upload_fileobj(file, ExtraArgs={'ACL': 'public-read'})
                    image_url = f"https://my-student.s3.amazonaws.com/{filename}"
                try:
                    cursor.execute(insert_sql,(name,gname,dob,password,image_url))
                    db_conn.commit()
                    query = "SELECT MAX(Roll) FROM data"
                    cursor.execute(query)
                    Rollno = cursor.fetchone()[0]
                except Exception as a:
                    return str(a)
            except Exception as e:
                return str(e)
            finally:
                cursor.close()
            print("all Done")
    
            return render_template("registration_completed.html", name=name,roll=Rollno,image_url=image_url)
        else:
            return "Access denied."
    except Exception as e:
        return str(e)
        

# def hash_password(password):
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
#     return hashed_password

if __name__=="__main__":
    app.run(debug=True)