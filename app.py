import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Folder for storing files
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt', 'xlsx'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50))
    tags = db.Column(db.String(200))
    material = db.Column(db.String(100), nullable=True)
    color = db.Column(db.String(50), nullable=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

class ItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    category = SelectField('Category', choices=[('screw', 'Screw'), ('resistor', 'Resistor'), ('filament', 'Filament'), ('other', 'Other')])
    location = StringField('Location')
    tags = StringField('Tags (comma-separated)')
    material = SelectField('Material', choices=[(None, 'None'), ('stainless_304', 'Stainless 304'), ('pla', 'PLA'), ('petg', 'PETG'), ('petgcf', 'PETG-CF')])
    color = SelectField('Color', choices=[(None, 'None'), ('black', 'Black'), ('orange', 'Orange'), ('grey', 'Grey'), ('white', 'White'), ('red', 'Red'), ('green', 'Green'), ('purple', 'Purple')])
    submit = SubmitField('Save')

class DocumentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    category = SelectField('Category', choices=[('technical_drawing', 'Technical Drawing'), ('datasheet', 'Datasheet')])
    file = StringField('File')
    submit = SubmitField('Upload')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    materials_needed = StringField('Materials Needed', validators=[DataRequired()])  # Comma-separated list
    submit = SubmitField('Create Project')

@app.route('/', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/inventory', methods=['GET'])
def inventory():
    query = request.args.get('search', '')
    items = Item.query.filter(Item.name.contains(query) | Item.tags.contains(query)).all()
    form = ItemForm()  # Create an instance of the form
    return render_template('inventory.html', items=items, query=query, form=form)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    form = ItemForm()
    if form.validate_on_submit():
        new_item = Item(
            name=form.name.data,
            quantity=form.quantity.data,
            category=form.category.data,
            location=form.location.data,
            tags=form.tags.data,
            material=form.material.data if form.material.data != 'None' else None,  # Handle 'None' as no material
            color=form.color.data if form.color.data != 'None' else None  # Handle 'None' as no color
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('add_item.html', form=form)

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    if form.validate_on_submit():
        item.name = form.name.data
        item.quantity = form.quantity.data
        item.category = form.category.data
        item.location = form.location.data
        item.tags = form.tags.data
        item.material = form.material.data if form.material.data != 'None' else None  # Handle 'None' as no material
        item.color = form.color.data if form.color.data != 'None' else None  # Handle 'None' as no color
        db.session.commit()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('edit_item.html', form=form, item=item)


@app.route('/use/<int:item_id>', methods=['GET', 'POST'])
def use_item(item_id):
    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        action = request.form['action']

        if action == "take":
            if item.quantity >= quantity:
                item.quantity -= quantity
            else:
                flash("Not enough stock available!", "danger")
        elif action == "add":
            item.quantity += quantity

        db.session.commit()
        return redirect(url_for('inventory'))

    return render_template('use_item.html', item=item)

@app.route('/delete_item/<int:item_id>', methods=['GET', 'POST'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted!', 'danger')
    return redirect(url_for('inventory'))

@app.route('/documents', methods=['GET'])
def documents():
    query = request.args.get('search', '')  # Get the search query from the URL
    documents = Document.query.filter(Document.name.contains(query) | Document.category.contains(query)).all()
    form = DocumentForm()
    return render_template('documents.html', documents=documents, query=query, form=form)


@app.route('/upload_document', methods=['GET', 'POST'])
def upload_document():
    form = DocumentForm()
    if form.validate_on_submit():
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Full path for saving

            file.save(file_path)

            document = Document(
                name=form.name.data,
                category=form.category.data,
                file_path=filename  # Store only the filename, not the full path
            )
            db.session.add(document)
            db.session.commit()
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('documents'))
        else:
            flash('Invalid file type.', 'danger')
    return render_template('upload_document.html', form=form)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/uploads/<path:filename>')
def download_document(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/edit_document/<int:document_id>', methods=['GET', 'POST'])
def edit_document(document_id):
    document = Document.query.get_or_404(document_id)  # Get the document by ID
    form = DocumentForm(obj=document)  # Initialize form with the document data

    if form.validate_on_submit():  # If the form is submitted and valid
        document.name = form.name.data  # Update document's name
        document.category = form.category.data  # Update document's category
        db.session.commit()  # Commit changes to the database
        flash('Document updated successfully!', 'success')  # Show success message

        return redirect(url_for('documents'))  # Redirect to documents list
    else:
        # Debugging: print the form errors to understand what's wrong
        print(form.errors)

    return render_template('edit_document.html', form=form, document=document)  # Render the template with form

@app.route('/projects', methods=['GET'])
def projects():
    query = request.args.get('search', '')  # Get the search query
    projects = Project.query.filter(Project.name.contains(query) | Project.description.contains(query)).all()
    return render_template('projects.html', projects=projects, query=query)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project = Project(
            name=form.name.data,
            description=form.description.data,
            materials_needed=form.materials_needed.data
        )
        db.session.add(new_project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('add_project.html', form=form)

@app.route('/use_item_in_project/<int:project_id>', methods=['GET'])
def use_item_in_project(project_id):
    project = Project.query.get_or_404(project_id)
    materials = project.materials_needed.split(',')
    for material in materials:
        item = Item.query.filter_by(name=material.strip()).first()
        if item and item.quantity > 0:
            item.quantity -= 1
            db.session.commit()
    flash('Materials updated for the project!', 'success')
    return redirect(url_for('projects'))


@app.route('/delete_document/<int:document_id>', methods=['GET', 'POST'])
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.file_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(document)
    db.session.commit()
    flash('Document deleted!', 'danger')
    return redirect(url_for('documents'))

@app.route('/delete_project/<int:project_id>', methods=['GET', 'POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)

    try:
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted successfully!', 'success')
    except:
        db.session.rollback()
        flash('There was an issue deleting the project.', 'danger')

    return redirect(url_for('projects'))

if __name__ == '__main__':
    app.run(debug=True)