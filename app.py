from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from io import BytesIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from models import db, Users, Break, Category, Exercices, Program, ProgramDetails
import logging

app = Flask(__name__)

UPLOAD_IMAGES_FOLDER = 'static/thumbnails'
UPLOAD_USERS_IMAGES_FOLDER = 'static/users'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_VIDEO_FOLDER = 'videos'
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
app.config['UPLOAD_IMAGES_FOLDER'] = UPLOAD_IMAGES_FOLDER
app.config['UPLOAD_VIDEO_FOLDER'] = UPLOAD_VIDEO_FOLDER
app.config['UPLOAD_USERS_IMAGES_FOLDER'] = UPLOAD_USERS_IMAGES_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/urbangymtest'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '53cR3t_K3y'
db.init_app(app)
# Directories
VIDEO_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
# Function to get MAC address from IP
def get_mac(ip_address):
    if ip_address == "127.0.0.1":  # Localhost case
        import uuid
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8 * 6, 8)][::-1])
        return mac
    else:
        arp_output = os.popen(f'arp -a {ip_address}').read()
        for line in arp_output.split('\n'):
            if ip_address in line:
                mac_address = line.split()[1]
                return mac_address
    return None
################################## Index #################################################
# Route to display message and button or welcome user
@app.route('/')
def index():
    ip_address = request.remote_addr
    mac_address = get_mac(ip_address)
    users = Users.query.all()
    for user in users:
        if not user.expire_date:
                user.expire_date = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    if mac_address:
        user = Users.query.filter_by(mac_address=mac_address).first()
        if user:
            if user.is_confirmed:
                if user.is_admin:
                    # Count unconfirmed users
                    unconfirmed_count = Users.query.filter_by(is_confirmed=False).count()
                    today = datetime.utcnow().date()

                    # Query for users with expiration date <= today or tomorrow
                    expired_program_count = (
                        Users.query.filter(Users.expire_date <= today + timedelta(days=1))
                        .filter(Users.is_confirmed == True)
                        .count()  # Use .count() directly on the query
                    )
                    return render_template('admin.html', user=user, unconfirmed_count=unconfirmed_count,expired_program_count=expired_program_count)
                else:
                    days = (
                        ProgramDetails.query.filter_by(program_id=user.program_id)
                        .with_entities(ProgramDetails.day)
                        .distinct()
                        .order_by(ProgramDetails.day)
                        .all()
                    )
                    return render_template('index.html', user=user, days=[d[0] for d in days])
            else:
                return render_template('status.html', success=True, message='Your account is pending admin confirmation. Please check back later.')
        else:
            session['mac_address'] = mac_address
            return redirect(url_for('register'))
    else:
        return 'MAC address could not be found.'


################################# Users Management ##################################################

@app.route('/admin/confirm/<int:user_id>', methods=['POST'])
def confirm_user(user_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    user = Users.query.get_or_404(user_id)
    user.is_confirmed = True
    try:
        db.session.commit()
        return redirect(url_for('unconfirmed_users'))
    except Exception as e:
        db.session.rollback()
        return f'An error occurred while confirming the user: {e}', 500

@app.route('/admin/unconfirm/<int:user_id>', methods=['POST'])
def unconfirm_user(user_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    user = Users.query.get_or_404(user_id)
    user.is_confirmed = False
    try:
        db.session.commit()
        return redirect(url_for('confirmed_users'))
    except Exception as e:
        db.session.rollback()
        return f'An error occurred while confirming the user: {e}', 500

@app.route('/admin/confirmed', methods=['GET'])
def confirmed_users():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    confirmed_users = Users.query.filter_by(is_confirmed=True).all()
    programs = Program.query.all()
    return render_template('confirmed_users.html', confirmed_users=confirmed_users,programs=programs)

@app.route('/admin/expired_program', methods=['GET'])
def expired_program_users():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    # Current date
    today = datetime.utcnow().date()

    # Query for users with expiration date <= today or tomorrow
    confirmed_users = (
        Users.query.filter(Users.expire_date <= today + timedelta(days=1))
        .filter(Users.is_confirmed == True)  # Only confirmed users
        .order_by(Users.expire_date.asc())  # Sort by expiration date
        .all()
    )

    programs = Program.query.all()
    return render_template('confirmed_users.html', confirmed_users=confirmed_users, programs=programs)

@app.route('/edit_user_confimed/<int:user_id>', methods=['GET', 'POST'])
def edit_user_conf(user_id):
    user = Users.query.get_or_404(user_id)    
    if request.method == 'POST':
            user.name = request.form['name']
            user.familyName = request.form['familyName']
            user.gender = request.form['gender']
            user.is_admin = 'is_admin' in request.form
            user.remarks = request.form.get('remarks', '')
            user.program_id = int(request.form['program_id'])
            user.dateOfBirth = request.form['dob']
            user.expire_date = request.form['exd']

            # Handle file upload for UserImage
            if 'UserImage' in request.files:
                user_photo = request.files['UserImage']
                if user_photo and allowed_file(user_photo.filename):
                    # Secure filename and save file
                    user_photo_filename = secure_filename(user_photo.filename)
                    user_photo_path = os.path.join(app.config['UPLOAD_USERS_IMAGES_FOLDER'], user_photo_filename)
                    user_photo.save(user_photo_path)
                    user.Photo = user_photo_filename
                else:
                    return "Invalid file type. Allowed types: png, jpg, jpeg, gif."
            else:
                return "No file uploaded for UserImage."

            # Commit changes to the database
            db.session.commit()
            return redirect(url_for('confirmed_users')) 
    # Render the edit form with current user data
    programs = Program.query.all()  # Fetch available programs if needed
    return render_template('edit_user_conf.html', user=user, programs=programs)

@app.route('/admin/unconfirmed', methods=['GET'])
def unconfirmed_users():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403
    unconfirmed_users = Users.query.filter_by(is_confirmed=False).all()
    return render_template('unconfirmed_users.html', unconfirmed_users=unconfirmed_users)



@app.route('/edit_user_unconfirmed/<int:user_id>', methods=['GET', 'POST'])
def edit_user_unconf(user_id):
    user = Users.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # Update user attributes from the form
            user.name = request.form['name']
            user.familyName = request.form['familyName']
            user.gender = request.form['gender']
            user.is_admin = 'is_admin' in request.form
            user.remarks = request.form.get('remarks', '')
            user.program_id = int(request.form['program_id'])
            user.dateOfBirth = request.form['dob']
            user.expire_date = request.form['exd']

            # Handle file upload for UserImage
            if 'UserImage' in request.files:
                user_photo = request.files['UserImage']
                if user_photo and allowed_file(user_photo.filename):
                    # Secure filename and save file
                    user_photo_filename = secure_filename(user_photo.filename)
                    user_photo_path = os.path.join(app.config['UPLOAD_USERS_IMAGES_FOLDER'], user_photo_filename)
                    user_photo.save(user_photo_path)
                    user.Photo = user_photo_filename
                else:
                    return "Invalid file type. Allowed types: png, jpg, jpeg, gif."
            else:
                return "No file uploaded for UserImage."

            # Commit changes to the database
            db.session.commit()
            return redirect(url_for('unconfirmed_users'))

        except Exception as e:
            db.session.rollback()  # Rollback changes if an error occurs
            return f"An error occurred: {str(e)}"

    # Render the edit form with current user data
    programs = Program.query.all()
    return render_template('edit_user_unconf.html', user=user, programs=programs)


#################################### Register ################################################
@app.route('/register', methods=['GET', 'POST'])
def register():
    #mac_address = session.get('mac_address')  # Retrieve the mac_address from the session
    ip_address = request.remote_addr
    mac_address = get_mac(ip_address)
    user = Users.query.filter_by(mac_address=mac_address).first()
    if user:
        return redirect(url_for('index'))
    if not mac_address:
        return redirect(url_for('index'))  # If no MAC address in session, redirect to home page

    if request.method == 'POST':
        name = request.form['name']
        familyName = request.form['Familyname']
        gender = request.form['gender']
        dateOfBirth=request.form['dob']
        new_user = Users(mac_address=mac_address, name=name, is_confirmed=False, is_admin=False, program_id=1, gender=gender, dateOfBirth=dateOfBirth ,familyName=familyName)

        try:
            db.session.add(new_user)
            db.session.commit()
            return render_template('status.html', success=True, message='Registration successful! Please wait for admin approval.')
        except Exception as e:
            db.session.rollback()
            return render_template('status.html', success=False, message=f'An error occurred while adding the user: {e}')

    return render_template('register.html', mac_address=mac_address)

############################# Watch #################################
@app.route('/day/<int:day>')
def view_day(day):
    ip_address = request.remote_addr
    mac_address = get_mac(ip_address)
    user = Users.query.filter_by(mac_address=mac_address).first()
    if not user:
        return redirect(url_for('index'))
    if not user.program_id:
        return 'No program assigned to the you yet !.', 400
    # Retrieve categories for the day
    categories = (
        ProgramDetails.query.filter_by(program_id=user.program_id, day=day, type='exercise')
        .join(Exercices, ProgramDetails.exercice_code == Exercices.code)
        .join(Category, Exercices.category_id == Category.Id)
        .with_entities(Category.Id, Category.name, Category.icone_Path, Category.icone_Path_female)
        .distinct()
        .all()
    )
    return render_template('categories.html', day=day, categories=categories, gender=user.gender)


@app.route('/category/<int:category_id>/day/<int:day>')
def view_category(category_id, day):
    #user = Users.query.filter_by(mac_address=session.get('mac_address')).first()
    ip_address = request.remote_addr
    mac_address = get_mac(ip_address)
    user = Users.query.filter_by(mac_address=mac_address).first()
    if not user:
        return redirect(url_for('index'))
    if not user.program_id:
        return 'No program assigned to you yet !.', 400
    exercices = (
        ProgramDetails.query.filter_by(program_id=user.program_id, day=day, type='exercise')
        .join(Exercices, ProgramDetails.exercice_code == Exercices.code)
        .filter(Exercices.category_id == category_id)
        .with_entities(
            Exercices.name,
            Exercices.videoPath,
            Exercices.videoPath_female
        )
        .order_by(ProgramDetails.sequence)
        .all()
    )
    video_files = [
        v_ex[1] if user.gender == 'male' else v_ex[2] for v_ex in exercices
    ]
    # Store the list of videos in the session
    session['video_list'] = video_files

    # Redirect to the first video in the list
    if video_files:
        return redirect(url_for('watch_video', filename=video_files[0]))

    return 'No videos available for this category.', 404


@app.route('/watch/<filename>')
def watch_video(filename):
    #user = Users.query.filter_by(mac_address=session.get('mac_address')).first()
    ip_address = request.remote_addr
    mac_address = get_mac(ip_address)
    user = Users.query.filter_by(mac_address=mac_address).first()
    if not user:
        return redirect(url_for('index'))

    # Get the full list of videos (stored in session or query)
    videos = session.get('video_list', [])
    if not videos:
        return 'No videos found in session.', 404

    return render_template('watch.html', videos=videos, filename=filename)


@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_DIRECTORY, filename)
##########################  EXERCICES  ################################
@app.route('/admin/exercises', methods=['GET'])
def manage_exercises():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    category_filter = request.args.get('category', type=int)
    name_or_code_filter = request.args.get('search', type=str)

    # Join the Exercices table with the Category table
    query = db.session.query(Exercices, Category.name.label('category_name')).join(Category, Exercices.category_id == Category.Id)

    if category_filter:
        query = query.filter(Exercices.category_id == category_filter)
    if name_or_code_filter:
        query = query.filter(
            or_(
                Exercices.name.like(f"%{name_or_code_filter}%"),
                Exercices.code.like(f"%{name_or_code_filter}%")
            )
        )

    exercises = query.all()
    categories = Category.query.all()

    return render_template('manage_exercises.html', exercises=exercises, categories=categories)
####################################################### programs  ##########################################################
@app.route('/admin/programs', methods=['GET', 'POST'])
def manage_programs():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    if request.method == 'POST':
        name = request.form.get('name')
        creator = request.form.get('creator')
        if name and creator:
            new_program = Program(name=name, creator=creator)
            db.session.add(new_program)
            db.session.commit()
#            flash('Program added successfully!', 'success')
 #       else:
  #          flash('Please fill in all fields!', 'danger')
        return redirect(url_for('manage_programs'))

    # Filters
    creator_filter = request.args.get('creator', type=str)
    name_filter = request.args.get('name', type=str)

    query = Program.query
    if creator_filter:
        query = query.filter(Program.creator.like(f"%{creator_filter}%"))
    if name_filter:
        query = query.filter(Program.name.like(f"%{name_filter}%"))

    programs = query.all()
    return render_template('manage_programs.html', programs=programs)

@app.route('/admin/programs/delete/<int:program_id>', methods=['POST'])
def delete_programs(program_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    program = Program.query.get_or_404(program_id)

    try:
        db.session.delete(program)
        db.session.commit()
        return redirect(url_for('manage_programs'))
    except Exception as e:
        db.session.rollback()
        return f"Error deleting program: {e}"

@app.route('/admin/programs/<int:program_id>/details', methods=['GET', 'POST'])
def program_details(program_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    program = Program.query.get_or_404(program_id)
    existing_exercises = Exercices.query.all()  # Assuming you have an `Exercise` model with `code` and `name`
    existing_categories = Category.query.all()  

    # Create a dictionary for quick lookup of exercise names by code
    exercise_map = {exercise.code: (exercise.name, exercise.category_id) for exercise in existing_exercises}
    category_map = {cat.Id: cat.name for cat in existing_categories}

    if request.method == 'POST':
        exercice_code = request.form.get('exercice_code')
        sequence = request.form.get('sequence', type=int)
        day = request.form.get('day', type=int)

        if sequence == 'end':
            max_sequence = (
                ProgramDetails.query.filter_by(program_id=program_id, day=day)
                .with_entities(db.func.max(ProgramDetails.sequence))
                .scalar() or 0
            )
            sequence = max_sequence + 1
        else:
            ProgramDetails.query.filter_by(program_id=program_id, day=day)\
                .filter(ProgramDetails.sequence >= sequence)\
                .update({ProgramDetails.sequence: ProgramDetails.sequence + 1}, synchronize_session=False)

        new_detail = ProgramDetails(
            program_id=program_id,
            exercice_code=exercice_code,
            break_id=None,
            sequence=sequence,
            day=day,
            type='exercise'
        )
        db.session.add(new_detail)
        db.session.commit()
        return redirect(url_for('program_details', program_id=program_id))

    # Fetch all details and include exercise names and categories
    details = ProgramDetails.query.filter_by(program_id=program_id)\
        .order_by(ProgramDetails.day, ProgramDetails.sequence).all()

    # Add names and categories to each detail
    details_with_names = [
        {
            "sequence": detail.sequence,
            "day": detail.day,
            "code": detail.exercice_code,
            "name": exercise_map.get(detail.exercice_code, ("Unknown", None))[0],
            "category": category_map.get(
                exercise_map.get(detail.exercice_code, ("Unknown", None))[1],
                "Unknown"
            )
        }
        for detail in details
    ]
    data = {
        category.name: [
            {"code": exercise.code, "name": exercise.name}
            for exercise in category.exercises
        ]
        for category in Category.query.all()
    }
    return render_template('program_details.html', program=program, details=details_with_names, existing_exercises=existing_exercises, data=data)




@app.route('/admin/programs/<int:program_id>/remove_exercise', methods=['POST'])
def remove_exercise(program_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    exercice_code = request.form.get('exercice_code')
    sequence = request.form.get('sequence', type=int)
    day = request.form.get('day', type=int)

    # Retrieve the specific exercise to delete
    exercise_to_delete = ProgramDetails.query.filter_by(
        program_id=program_id,
        exercice_code=exercice_code,
        sequence=sequence,
        day=day
    ).first()

    if exercise_to_delete:
        db.session.delete(exercise_to_delete)

        # Adjust the sequence of subsequent exercises
        ProgramDetails.query.filter_by(program_id=program_id, day=day)\
            .filter(ProgramDetails.sequence > sequence)\
            .update({ProgramDetails.sequence: ProgramDetails.sequence - 1}, synchronize_session=False)

        db.session.commit()

        #flash('Exercise removed successfully!', 'success')
    #else:
     #   flash('Exercise not found.', 'danger')

    return redirect(url_for('program_details', program_id=program_id))



###########################  #################################
@app.route('/admin/exercises/add', methods=['GET', 'POST'])
def add_exercise():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    if request.method == 'POST':
        # Form data
        name = request.form['name']
        category_id = request.form['category']
        description = request.form['description']
        video_file = request.files['video_path']
        video_file_f = request.files['video_path_female']
        # Validate video file
        if not (video_file and allowed_video_file(video_file.filename)):
            error_message = "Invalid file for video. Only video files are allowed."
            categories = Category.query.all()
            return render_template('add_exercise.html', categories=categories, error=error_message)
        if not (video_file_f and allowed_video_file(video_file_f.filename)):
            error_message = "Invalid file for video. Only video files are allowed."
            categories = Category.query.all()
            return render_template('add_exercise.html', categories=categories, error=error_message)

        # Secure filename and save the file
        video_filename = secure_filename(video_file.filename)
        video_path = os.path.join(app.config['UPLOAD_VIDEO_FOLDER'], video_filename)
        video_f_filename = secure_filename(video_file_f.filename)
        video_f_path = os.path.join(app.config['UPLOAD_VIDEO_FOLDER'], video_f_filename)

        try:
            # Save the video file to the server
            video_file.save(video_path)
            video_file_f.save(video_f_path)
            # Fetch the category and generate the exercise code
            category = Category.query.get(category_id)
            if not category:
                raise ValueError("Invalid category ID")

            # Generate a unique exercise code
            instance_count = len(category.exercises)
            code = f"{category.name[:2].upper()}_{name[:1].upper()}_{instance_count + 1}"

            # Create the new exercise
            exercise = Exercices(
                code=code,
                name=name,
                category_id=category_id,
                description=description,
                videoPath=video_filename,
                videoPath_female=video_f_filename
            )

            # Increment the number of instances in the category
            category.numberOfInstances += 1

            # Add and commit the exercise
            db.session.add(exercise)
            db.session.commit()

            return redirect(url_for('manage_exercises'))
        except Exception as e:
            db.session.rollback()
            error_message = f"An error occurred: {str(e)}"
            categories = Category.query.all()
            return render_template('add_exercise.html', categories=categories, error=error_message)

    # GET request: Render the form
    categories = Category.query.all()
    return render_template('add_exercise.html', categories=categories)
@app.route('/admin/exercises/edit/<string:code>', methods=['GET', 'POST'])
def edit_exercise(code):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    exercise = Exercices.query.get_or_404(code)
    if request.method == 'POST':
        exercise.name = request.form['name']
        exercice_category= request.form['category']
        exercise.description = request.form['description']
        video_file = request.files.get('videoPath')
        video_file_f = request.files.get('video_path_female')

        try:
            if exercice_category != exercise.category_id :
                category = Category.query.get_or_404(exercise.category_id)
                category.numberOfInstances = (
                Exercices.query.filter_by(category_id=category.Id).count() - 1
                     )
                category = Category.query.get_or_404(exercice_category)
                category.numberOfInstances = (
                Exercices.query.filter_by(category_id=category.Id).count() + 1
                )
                exercise.category_id = exercice_category
            # Handle male version video file
            if video_file and allowed_video_file(video_file.filename):
                video_filename = secure_filename(video_file.filename)
                video_path = os.path.join(app.config['UPLOAD_VIDEO_FOLDER'], video_filename)
                
                # Delete old video if it exists
                if exercise.videoPath:
                    old_video_path = os.path.join(app.config['UPLOAD_VIDEO_FOLDER'], exercise.videoPath)
                    if os.path.exists(old_video_path):
                        os.remove(old_video_path)

                video_file.save(video_path)
                exercise.videoPath = video_filename  # Update with new file name

            # Handle female version video file
            if video_file_f and allowed_video_file(video_file_f.filename):
                video_f_filename = secure_filename(video_file_f.filename)
                video_f_path = os.path.join(app.config['UPLOAD_VIDEO_FOLDER'], video_f_filename)
                
                # Delete old female video if it exists
                if exercise.videoPath_female:
                    old_video_f_path = os.path.join(app.config['UPLOAD_VIDEO_FOLDER'], exercise.videoPath_female)
                    if os.path.exists(old_video_f_path):
                        os.remove(old_video_f_path)

                video_file_f.save(video_f_path)
                exercise.videoPath_female = video_f_filename  # Update with new file name

            # Save changes to the database
            db.session.commit()
            return redirect(url_for('manage_exercises'))

        except Exception as e:
            db.session.rollback()
            return f'Error: {e}'

    categories = Category.query.all()
    return render_template('edit_exercise.html', exercise=exercise, categories=categories)

@app.route('/admin/exercises/delete/<string:code>', methods=['POST'])
def delete_exercise(code):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    try:
        # Fetch the exercise
        exercise = Exercices.query.get_or_404(code)

        # Update category instance count
        category = Category.query.get_or_404(exercise.category_id)
        category.numberOfInstances = (
            Exercices.query.filter_by(category_id=category.Id).count() - 1
        )

        # Delete video file from the file system
        if exercise.videoPath:
            video_path = os.path.join(app.config['UPLOAD_VIDEO_FOLDER'], exercise.videoPath)
            if os.path.exists(video_path):
                os.remove(video_path)

        # Delete the exercise from the database
        db.session.delete(exercise)
        db.session.commit()

        return redirect(url_for('manage_exercises'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting exercise {code}: {e}')
        return 'An error occurred.', 500

########################### Categories  ######################################
@app.route('/admin/categories', methods=['GET'])
def manage_categories():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    categories = Category.query.all()
    return render_template('manage_categories.html', categories=categories)


@app.route('/admin/categories/add', methods=['GET', 'POST'])
def add_category():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    if request.method == 'POST':
        name = request.form['name']

        male_image = request.files['icone_Path']
        female_image = request.files['icone_Path_female']

        if not (male_image and allowed_file(male_image.filename)):
            return "Invalid file for male image. Only images are allowed."
        if not (female_image and allowed_file(female_image.filename)):
            return "Invalid file for female image. Only images are allowed."

        # Secure filenames and save the files
        male_filename = secure_filename(male_image.filename)
        female_filename = secure_filename(female_image.filename)

        male_image_path = os.path.join(app.config['UPLOAD_IMAGES_FOLDER'], male_filename)
        female_image_path = os.path.join(app.config['UPLOAD_IMAGES_FOLDER'], female_filename)

        try:
            male_image.save(male_image_path)
            female_image.save(female_image_path)

            # Save to database
            category = Category(
                name=name,
                numberOfInstances=0,
                icone_Path=male_filename,
                icone_Path_female=female_filename
            )
            db.session.add(category)
            db.session.commit()
            return redirect(url_for('manage_categories'))
        except Exception as e:
            db.session.rollback()
            return f"Error adding category: {e}"

    return render_template('add_category.html')


    

@app.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        category.name = request.form['name']
        male_image = request.files['icone_Path']
        female_image = request.files['icone_Path_female']
        if not (male_image and allowed_file(male_image.filename)):
            return "Invalid file for male image. Only images are allowed."
        if not (female_image and allowed_file(female_image.filename)):
            return "Invalid file for female image. Only images are allowed."

        # Secure filenames and save the files
        male_filename = secure_filename(male_image.filename)
        female_filename = secure_filename(female_image.filename)

        male_image_path = os.path.join(app.config['UPLOAD_IMAGES_FOLDER'], male_filename)
        female_image_path = os.path.join(app.config['UPLOAD_IMAGES_FOLDER'], female_filename)
        try:
            male_image.save(male_image_path)
            female_image.save(female_image_path)
            category.icone_Path=male_filename
            category.icone_Path_female=female_filename
            db.session.commit()
            return redirect(url_for('manage_categories'))
        except Exception as e:
            db.session.rollback()
            return f"Error updating category: {e}"

    return render_template('edit_category.html', category=category)

@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    category = Category.query.get_or_404(category_id)

    try:
        db.session.delete(category)
        db.session.commit()
        return redirect(url_for('manage_categories'))
    except Exception as e:
        db.session.rollback()
        return f"Error deleting category: {e}"
####################################### BREAKS #################################################
@app.route('/admin/breaks', methods=['GET'])
def manage_breaks():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    breaks = Break.query.all()
    return render_template('manage_breaks.html', breaks=breaks)
@app.route('/admin/breaks/add', methods=['GET', 'POST'])
def add_break():
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    if request.method == 'POST':
        duration = request.form['duration']
        vid_path = request.form['vid_path']

        try:
            new_break = Break(duration=duration, VidPath=vid_path)
            db.session.add(new_break)
            db.session.commit()
            return redirect(url_for('manage_breaks'))
        except Exception as e:
            db.session.rollback()
            return f"Error adding break: {e}"

    return render_template('add_break.html')
@app.route('/admin/breaks/edit/<int:break_id>', methods=['GET', 'POST'])
def edit_break(break_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    break_item = Break.query.get_or_404(break_id)

    if request.method == 'POST':
        break_item.duration = request.form['duration']
        break_item.VidPath = request.form['vid_path']

        try:
            db.session.commit()
            return redirect(url_for('manage_breaks'))
        except Exception as e:
            db.session.rollback()
            return f"Error updating break: {e}"

    return render_template('edit_break.html', break_item=break_item)
@app.route('/admin/breaks/delete/<int:break_id>', methods=['POST'])
def delete_break(break_id):
    if request.remote_addr != "127.0.0.1":
        return 'Access denied: Admin functionality is restricted to the server machine only.', 403

    break_item = Break.query.get_or_404(break_id)

    try:
        db.session.delete(break_item)
        db.session.commit()
        return redirect(url_for('manage_breaks'))
    except Exception as e:
        db.session.rollback()
        return f"Error deleting break: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
