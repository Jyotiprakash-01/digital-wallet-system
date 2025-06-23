from decimal import Decimal
import os
import base64
import requests
from flask import Flask,request,jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone

load_dotenv()
app=Flask(__name__)
bcrypt=Bcrypt(app)
db_host=os.environ['db_host']
db_username=os.environ['db_username']
db_password=os.environ['db_password']
db_name=os.environ['db_name']
api_key=os.environ['api_key']

EXCHANGE_API_URL="https://api.currencyapi.com/v3/latest?apikey=cur_live_Tws4DFUCPSQHb0aEhsfUq60q4Mk1bMm4e0ktlhck&currencies=INR%2CUSD%2CEUR"
app.config['SQLALCHEMY_DATABASE_URI']="mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}".format(db_username=db_username,db_password=db_password,db_host=db_host,db_name=db_name)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db=SQLAlchemy(app)

class User(db.Model):
    user_id=db.Column(db.Integer,primary_key=True)
    user_name=db.Column(db.String(30),unique=True,nullable=False)
    user_password=db.Column(db.String(256),nullable=False)
    user_balance=db.Column(db.Numeric(10,2),unique=False,default=Decimal('0.00'),nullable=False)

class TransactionHistory(db.Model):
    user_id=db.Column(db.Integer,db.ForeignKey(User.user_id),nullable=False)
    transaction_id=db.Column(db.Integer,primary_key=True)
    kind=db.Column(db.String(10),nullable=False)
    amt=db.Column(db.Integer,nullable=False)
    updated_bal=db.Column(db.Numeric(10,2),unique=False,nullable=False)
    timestamp=db.Column(db.DateTime,default=datetime.now(timezone.utc))


class Product(db.Model):
    product_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey(User.user_id),nullable=False)    
    product_name=db.Column(db.String(20))
    price=db.Column(db.Numeric(10,2),nullable=False)
    product_description=db.Column(db.String(200),nullable=True)
    

@app.route('/register',methods=['POST'])
def registerUser():
    data=request.get_json()

    username=data.get('username')
    password=data.get('password')
    try:
        user=User.query.filter_by(user_name=username).first()
        if not (user is None):
            return jsonify({"mssg":"User Already Exists"})
        if not username or not password:
            return jsonify({"mssg":"Either Username or Password is Missing"})
        print(data)
        
        try:
            hashed_password=bcrypt.generate_password_hash(password.strip()).decode('utf-8')
            print("Hashed",hashed_password)
        except Exception as e:
            return jsonify({"mssg":" Password cant be hashed" }),502 
        try:  
            new_user=User(user_name=username.strip(),user_password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"mssg":"User created successfully"}),201
        except Exception as e:
            db.session.rollback()
            return jsonify({"mssg":"User already Exists"}),400
    except Exception as e: 
        return jsonify({"mssg":"Internal Server Server"}),500
    
def authenticateUser(header):
    verified=False
    if not header or not header.startswith('Basic'):
        return jsonify({"status":verified,"mssg":"Header not present or Invalid"}),400
    encoded_header=header.split(" ")[1]
    try:
        
        decoded_bytes=base64.b64decode(encoded_header)
        
        decoded_credentials=decoded_bytes.decode("utf-8")
        
        username,password=decoded_credentials.split(":")
       
        
    except Exception as e:
        return jsonify({"status":verified,"mssg":"Could not Decode username or password"}),401
    
    user=User.query.filter_by(user_name=username).first()
    print(user)
    if not user:
        return jsonify({"status":verified,"mssg":"User does not Exists"}),404
    try:
        print("Hello 2")
        

        verified=bcrypt.check_password_hash(user.user_password,password)
        # print(verified)
        
        return jsonify({"status":verified,"mssg":"User Exist and successfully logged in","User":user.user_id}),200
    except Exception as e:
        return jsonify({"status":verified,"mssg":"Password is not matching"}),400
    
@app.route('/product',methods=['POST'])
def addProducts():
    
    header=request.headers.get('Authorization')
    try:
        auth=authenticateUser(header)
        if isinstance(auth, tuple):
            response_obj, status_code = auth
            
        else:
            response_obj = auth
            status_code = 200
        response=response_obj.get_json()
        # print(response)
        userValidated=response.get('status')
        validationMssg=response.get('mssg')
    except Exception as e:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),status_code 
    
    print(validationMssg)

    # return jsonify({"status":validate,"str":response.get('mssg'),"mssg":"requests received"}),200
    if userValidated:
        data=request.get_json()
        name=data.get('name')
        user=response.get('User')
        print(user)
        amount=data.get('price')
        description=data.get('description')
        try:
            print("Hello 4")
            product=Product(product_name=name,user_id=user,price=amount,product_description=description)
            print(product)
            db.session.add(product)
            db.session.commit()
            return jsonify({"str":response.get('mssg'),"mssg":"Product Created By User"}),201
        except Exception as e:
            db.session.rollback()
            return jsonify({"mssg":"Could not add Product to db"}),400
    else:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),401 

@app.route("/fund",methods=["POST"])
def addBalance():
    header=request.headers.get('Authorization')
    try:
        auth=authenticateUser(header)
        if isinstance(auth, tuple):
            response_obj, status_code = auth
            
        else:
            response_obj = auth
            status_code = 200
        response=response_obj.get_json()
        # print(response)
        userValidated=response.get('status')
        validationMssg=response.get('mssg')
        userid=response.get('User')
        print("st",userid)
    except Exception as e:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),status_code 
    # print(validationMssg)


    if userValidated:
        try:
            user_obj=User.query.filter_by(user_id=userid).first()
            print("hello 7")
            print(user_obj)
        except Exception as e:
            return jsonify({"msg":"Server Could not find the user"}),502
        data=request.get_json()
        amount=data.get('amt')
        try:         
            print("hello 8")
            print(user_obj.user_balance)

            user_obj.user_balance+=Decimal(str(amount))
            db.session.commit()
            return jsonify({"msg":"Succesfully added balance to wallet"}),200
        except Exception as e:
            
            db.session.rollback()
            return jsonify({"msg":"Could not add balance to wallet"}),500
    else:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),401

@app.route('/pay',methods=['POST'])
def payBalance():
    header=request.headers.get('Authorization')
    try:
        auth=authenticateUser(header)
        if isinstance(auth, tuple):
            response_obj, status_code = auth
            
        else:
            response_obj = auth
            status_code = 200
        response=response_obj.get_json()
        # print(response)
        userValidated=response.get('status')
        validationMssg=response.get('mssg')
        userid=response.get('User')
        print("st",userid)
    except Exception as e:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),status_code 
    # print(validationMssg)


    if userValidated:
        data=request.get_json()
        payUserName=data.get('to')
        payAmount=data.get('amt')
        try:
            userCredited=User.query.filter_by(user_name=payUserName).first()
            userDebitted=User.query.filter_by(user_id=userid).first()
        except Exception as e:
            return jsonify({"mssg": "No user found"}),400
        try:
            if((userDebitted.user_balance-Decimal(str(payAmount)))<0.0):
                return jsonify({"mssg":"insufficient funds or recipient doesnot exist."}),400
            userCredited.user_balance+=Decimal(str(payAmount))
            userDebitted.user_balance-=Decimal(str(payAmount))
            db.session.commit()
            try:
                t1=TransactionHistory(user_id=userCredited.user_id,kind="credit",amt=Decimal(str(payAmount)),updated_bal=userCredited.user_balance)
                t2=TransactionHistory(user_id=userDebitted.user_id,kind="debit",amt=Decimal(str(payAmount)),updated_bal=userDebitted.user_balance)
                db.session.add(t1)
                db.session.add(t2)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({"mssg":"Transaction Sucessfully completed but failed to add to transaction history"}),500
            
            
            return jsonify({"mssg":"Transaction Sucessfully completed"}),200
        except Exception as e:
            db.session.rollback()
            return jsonify({"mssg":"Transaction failed."}),500
    else:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),401

@app.route('/stmt',methods=['GET'])
def transaction_history():
    header=request.headers.get('Authorization')
    try:
        auth=authenticateUser(header)
        if isinstance(auth, tuple):
            response_obj, status_code = auth
            
        else:
            response_obj = auth
            status_code = 200
        response=response_obj.get_json()
        # print(response)
        userValidated=response.get('status')
        validationMssg=response.get('mssg')
        userid=response.get('User')
        print("st",userid)
    except Exception as e:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),status_code 
    # print(validationMssg)


    if userValidated:
        try:
            result=[]
            transactions=TransactionHistory.query.filter_by(user_id=userid).all()
            if not transactions:
                return jsonify({"mssg":"No transaction found"}),404
            for t in transactions:
                result.append({
                    "kind":t.kind,
                    "amt":t.amt,
                    "updated_bal":t.updated_bal,
                    "timestamp":t.timestamp})
            return jsonify(result),200
        except Exception as e:
            return jsonify({"mssg":"Failed To fetch transactions"}),500
    else:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),401

@app.route('/product',methods=['GET'])
def getProduct():
    try:
        products=Product.query.all()
        if not products:
                return jsonify({"mssg":"No product found"}),404
        catalog=[]
        for p in products:
            catalog.append({
                "id": p.product_id,
                "name": p.product_name,
                "price": p.price,
                "description": p.product_description
            })
        return jsonify(catalog),200
    except Exception as e:
        return jsonify({"mssg":"Internal Server Error Could not Fetch products"}),500
    
@app.route('/buy',methods=['POST'])
def buyProduct():
   
    header=request.headers.get('Authorization')
    try:
        auth=authenticateUser(header)
        if isinstance(auth, tuple):
            response_obj, status_code = auth
            
        else:
            response_obj = auth
            status_code = 200
        response=response_obj.get_json()
        # print(response)
        userValidated=response.get('status')
        validationMssg=response.get('mssg')
        userid=response.get('User')
        print("st",userid)
    except Exception as e:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),status_code 
    # print(validationMssg)


    if userValidated:
        try:
            data=requests.get_json()
            pid=data.get('product_id')
            try:
                buyingUser=User.query.filter_by(user_id=userid).first()
                product=Product.query.filter_by(product_id=pid).first()
            except Exception as e:
                return jsonify({"mssg":"No such Product found"}),400

            if((buyingUser.user_balance-product.price)<0):
                return jsonify({"mssg":"insufficient funds or recipient doesnot exist."}),400
            
            buyingUser.user_balance-=product.price
            t=TransactionHistory(user_id=buyingUser.user_id,kind="debit",amt=product.price,updated_bal=buyingUser.user_balance)
            db.session.add(t)
            db.session.commit()
            return jsonify({"message":"Product Purchased","balance":buyingUser.user_balance}),200
        except Exception as e:
            db.session.rollback()
            print(str(e))
            return jsonify({"mssg":"Transaction Failed"}),400
    else:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),401
    


@app.route('/bal',methods=['GET'])
def checkBalanceInUsd():
    header=request.headers.get('Authorization')
    try:
        auth=authenticateUser(header)
        if isinstance(auth, tuple):
            response_obj, status_code = auth
            
        else:
            response_obj = auth
            status_code = 200
        response=response_obj.get_json()
        # print(response)
        userValidated=response.get('status')
        validationMssg=response.get('mssg')
        userid=response.get('User')
        print("st",userid)
    except Exception as e:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),status_code 
    # print(validationMssg)


    if userValidated:
        try:
           
            currency=request.args.get('currency','USD').upper()
            try:
                response=requests.get(EXCHANGE_API_URL)
                currencyData=response.json()
                # print("Hi 1")
                if response.status_code !=200 :
                    return jsonify({"mssg":"Failed to fetch exchange rates"}),502
            except Exception as e:
                print(str(e))
                return jsonify({"mssg":"Internal Server Error"}),500
            # print("Hi 2")
            rate=currencyData['data'].get(currency,{}).get('value')
            user=User.query.filter_by(user_id=userid).first()
            result={}
            result["balance"]=user.user_balance*Decimal(str(rate))
            result["currency"]=currency
            # print("Hi 3")
            return jsonify(result),200
        except Exception as e:
                print(str(e))
                return jsonify({"mssg":"Conversion Failed"}),500
    else:
        return jsonify({"mssg":"User not Authenticated", "reason":validationMssg}),502
            

                
@app.route('/')
def retString():
    return "Hello"

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
