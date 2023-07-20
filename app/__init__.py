from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import firestore
from firebase_admin import storage,credentials, auth
import stripe
import json
import os
from flask_cors import CORS


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Firebase credentials
cred = credentials.Certificate("service_key.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'cocmarketplace-6de0e.appspot.com'
})
db = firestore.client()
bucket = storage.bucket()

stripe.api_key = 'sk_test_51NTe9USEwRY11GwhYoQ7oD9ezip8Rj35dscC7t5kTbI2vBQLhD8kBGsnwxVe4LEVVa9pYDxRjC7tWFGjhz85X0hF00WOhG5bGW'



def delete_item(id):
    document_id = id

    # Retrieve the data for the deleted document (if needed)
    deleted_document = db.collection('data').document(document_id).get().to_dict()

    # Remove the document from Firestore
    db.collection('data').document(document_id).delete()

    # Delete the images from Firebase Storage
    if deleted_document:
        try:
            image1_url = deleted_document.get('image1_url')
            image2_url = deleted_document.get('image2_url')

            if image1_url:
                image1_blob = storage.bucket().blob(image1_url)
                image1_blob.delete()

            if image2_url:
                image2_blob = storage.bucket().blob(image2_url)
                image2_blob.delete()
        except:
            pass
    return True

def check_user_exists(uid):
    from firebase_admin import firestore
    try:
        user = auth.get_user(uid)
        print("User exists:", user.uid)
        return True
    except auth.AuthError as e:
        if e.code == 'user-not-found':
            print("User does not exist")
            return False
        else:
            # Handle other exceptions
            print("Error occurred:", e)
            return False

@app.route('/',methods=['GET'])
def home():
    return jsonify({'Status': 'Marketplace api Online'}), 200



@app.route('/profile/<id>',methods=['GET'])
def user_profile(id):
    uid = id
    try:
        if check_user_exists(uid=uid):
            pass
        else:
            return jsonify({'error': 'Invalid data or missing uid'}), 400
    except:
        return jsonify({'error': 'Invalid data or missing uid'}), 400
    users_ref = db.collection('users')

    # Query the collection based on the UID
    query = users_ref.where('uid', '==', uid)

    # Get the documents that match the query
    user_docs = query.get()
    # Retrieve the first matching document
    for doc in user_docs:
        res = doc.to_dict()
        if uid == 'HMPFyv15ZISU0B16nMCBrTKbv0p2':
            res['type'] = "admin"
        else:
            res['type'] = 'user'
        return {'status':True, "res":res},200

    # If no matching document found, return None or appropriate response
    return {"status": False, 'res':None},401



@app.route('/delete_data',methods=['POST'])
def delete_data():
    obj_id = request.json['obj_id']
    if delete_item(obj_id):
        return {'status':True,"description":'deleted'},200
    else:
        return {'status':False,"description":'not deleted'},501



# Endpoint to add data and images to Firebase
@app.route('/add_data', methods=['POST'])
def add_data():
    # try:
    uid = request.form.get('uid')
    title = request.form.get('title')
    description = request.form.get('description')
    price = int(request.form.get('price'))
    Type = request.form.get('type')
    email = request.form.get('email')
    password = request.form.get('password')
    image1 = request.files.get('image1')
    image2 = request.files.get('image2')

    # except:
    #     return {"status":False,"desc":"incorrect or imcomplete input"},400
    # if uid != uid:
    #     return False
    try:
        if check_user_exists(uid=uid):
            pass
        else:
            return jsonify({'error': 'Invalid data or missing fields'}), 400
    except:
        return jsonify({'error': 'Invalid data or missing fields'}), 400
    if uid == "HMPFyv15ZISU0B16nMCBrTKbv0p2":
        if title and description and email and password and Type and price and image1 and image2:
            # Upload image1 to Firebase Storage
            image1_blob = bucket.blob(image1.filename)
            image1_blob.upload_from_file(image1)

            image1_blob.make_public()

            # Upload image2 to Firebase Storage
            image2_blob = bucket.blob(image2.filename)
            image2_blob.upload_from_file(image2)

            image2_blob.make_public()

            # Get the public URLs of the uploaded images
            image1_url = image1_blob.public_url
            image2_url = image2_blob.public_url

            # Create the data object
            data = {
                'title': title,
                'description': description,
                'price': price,
                "type":Type,
                'email':email,
                'pasowrd':password,
                'image1_url': image1_url,
                'image2_url': image2_url
            }

            # Add data to Firebase "data" collection
            db.collection('data').add(data)

            return jsonify({'message': 'Data added successfully'}), 201
        else:
            print({
                't':title,
                'd':description,
                'p':price,
                'e': email,
                'pw' : password,
                'type':Type,
                'i1u': image1,
                'i2u': image2
            })
            return jsonify({'message': 'Incomplete data'}), 400
            
    else:
        return jsonify({'message': 'Login with admin please'}), 500

# Endpoint to retrieve data and images from Firebase
@app.route('/get_data', methods=['GET'])
def get_data():
    # try:
    data_ref = db.collection('data').get()
    items = db.collection("data").get()
    ids = [item.id for item in items]
    i = 0
    data = []
    for doc in data_ref:

        data_dict = doc.to_dict()
        try:
            del data_dict['email']
            del data_dict['password']
            print('deleted id passs while getting in frontend')
        except:
            pass
        try:
            data_dict['image1_url'] = data_dict['image1_url'] + '?alt=media'
            data_dict['image2_url'] = data_dict['image2_url'] + '?alt=media'
        except:
            data_dict['image1_url'] = "none"
            data_dict['image1_url'] = "none"
        data_dict['index'] = ids[i]
        i+=1
        data.append(data_dict)

    return jsonify(data), 200

@app.route('/cart/get', methods=['POST'])
def fetch_data():
    user_id = request.json['Uid']
    data = []
    print(user_id)


    try:
        if check_user_exists(uid=user_id):
            pass
        else:
            return jsonify({'error': 'Invalid data or missing uid'}), 400
    except:
        return jsonify({'error': 'Invalid data or missing uid'}), 400
    user_ref = db.collection('users')
    querry = user_ref.where('uid', '==', user_id)
    user_doc = querry.get()

    for doc in user_doc:
        # doc_ref = user_ref.document(doc.id)
        res = doc.to_dict()
        print(res)
        print(user_id)
        # try:
        cart = res['cart']
        for document_id in cart:

            data_ref = db.collection('data').document(document_id)
            data_doc = data_ref.get()

            if data_doc.exists:
                data_dict = data_doc.to_dict()
                data.append(data_dict)
            else:
                # Document not found
                data.append({})
            # except:
        #     pass
    return jsonify(data)

@app.route('/cart/modify', methods=['POST'])
def update_cart():
    try:
        user_id = request.json['user_id']
        cart_item = request.json['cart_item']
        action = request.json['action']
    except:
        print(request.json)
        return {'error': 'not propperly set requirement'},404
    # Check if the user exists
    try:
        if check_user_exists(uid=user_id):
            pass
        else:
            return jsonify({'error': 'Invalid data or missing uid'}), 400
    except:
        return jsonify({'error': 'Invalid data or missing uid'}), 400
    user_ref = db.collection('users')
    querry = user_ref.select(field_paths=[]).where('uid', '==', user_id)
    user_doc = querry.get()

        # Get the documents that match the query

    for doc in user_doc:
        doc_ref = user_ref.document(doc.id)
        res = doc.to_dict()
        print(res)
        try:
            cart = res['cart']
        except KeyError:
            cart = []

        if action == 'add':
            if cart_item not in cart:
                cart.append(cart_item)
        elif action == 'remove':
            if cart_item in cart:
                cart.remove(cart_item)

        # Update the cart in the user document
        doc_ref.update({'cart': cart})
        return {'message': 'Cart updated successfully'},200

# this is code

# querry.update({'cart': cart})
#     ^^^^^^^^^^^^^
# AttributeError: 'Query' object has no attribute 'update'

# how do i fix this error

@app.route('/add_to_owned_accounts', methods=['POST'])
def add_to_owned_accounts():
    user_id = request.json['user_id']
    document_id = request.json['document_id']

    try:
        if check_user_exists(uid=user_id):
            pass
        else:
            return jsonify({'error': 'Invalid data or missing uid'}), 400
    except:
        return jsonify({'error': 'Invalid data or missing uid'}), 400
    user_ref = db.collection('users')
    querry = user_ref.select(field_paths=[]).where('uid', '==', user_id)
    user_doc = querry.get()

        # Get the documents that match the query

    for doc in user_doc:
        doc_ref = user_ref.document(doc.id)
        res = doc.to_dict()
        print(res)
        try:
            bought = res['owned_accounts']
        except KeyError:
            bought = []
        data_ref = db.collection('data').document(document_id)
        data_doc = data_ref.get()
        if data_doc.exists:
            bought.append(data_doc.to_dict())

        # Update the "owned accounts" field in the user document
        doc_ref.update({'owned_accounts': bought})
        delete_item(document_id)
        return {
            'account':bought,
            'message': 'Document added to owned accounts successfully'},200
    else:
        return {'error': 'Document not found'},401



@app.route('/create-checkout-link', methods=['POST'])
def create_checkout_link():
    data = request.get_json()
    product_id = data.get('product_id')
    Uid = data.get('Uid')
    # product = db_pretend.get(product_id)

    data_ref = db.collection('data').document(product_id)
    data_doc = data_ref.get()

    if data_doc.exists:
        product = data_doc.to_dict()
    else:
        product = False
        return {"staus":False},500
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    price_data = {
        'currency': 'usd',
        'unit_amount': int(product['price'] * 100),
        'product_data': {
            'name': product['title'],
            'description': product['description'],
            'images': [product['image1_url']]
        }
    }


    # Create a Stripe checkout session
    session = stripe.checkout.Session.create(
        success_url = 'http://127.0.0.1:3000/success?id='+product_id+'&uid='+Uid,
        cancel_url  = 'http://127.0.0.1:3000/cancel',
        payment_method_types=['card'],
        mode='payment',
        line_items=[{
            'price_data': price_data,
            'quantity': 1
        }],
        client_reference_id=product_id,
        metadata={'product_id': product_id}

    )

    session_url = session.url
    webhook_url = 'http://localhost:5000/webhook'  # Replace with your webhook URL
    session_url_with_webhook = f'{session_url}&webhook_url={webhook_url}'

    print({'checkout_link': session_url_with_webhook})
    return jsonify({'checkout_link': session_url}), 200



# http://127.0.0.1:5000/webhook

# @app.route('/webhook', methods=['POST'])
# def handle_webhook():
#     payload = request.data

#     try:
#         event = stripe.Event.construct_from(
#             json.loads(payload), stripe.api_key
#         )

#         if event.type == 'checkout.session.completed':
#             session = event.data.object
#             product_id = session.metadata.get('product_id')
#             print("sessoion complete trigger")
#             print("sessoion - ", session)
#             print("product id - ", product_id)
#             # Trigger your callback function here using the product_id
#             # For example:
#             # callback_function(product_id)

#     except ValueError as e:
#         # Invalid payload
#         return jsonify({'error': str(e)}), 400

#     return jsonify({'success': True}), 200

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)

'''
python -m uvicorn Main:app --host 0.0.0.0 --port $PORT--reload
'''