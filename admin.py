from flask_admin import Admin, AdminIndexView, expose
from flask import redirect
from flask_login import current_user
from flask_admin.contrib.pymongo import ModelView as MongoModelView
from wtforms import Form, StringField, FloatField, IntegerField
from wtforms.validators import Optional, DataRequired, NumberRange
from extensions import mongo

class ExoplanetForm(Form):
    pl_name = StringField('Planet Name', validators=[DataRequired()])
    hostname = StringField('Host Star', validators=[DataRequired()])
    discoverymethod = StringField('Discovery Method', validators=[DataRequired()])
    disc_year = IntegerField('Discovery Year', validators=[Optional(), NumberRange(min=1900, max=2100)])
    pl_rade = FloatField('Planet Radius (Earth)', validators=[Optional(), NumberRange(min=0)])
    pl_bmasse = FloatField('Planet Mass (Earth)', validators=[Optional(), NumberRange(min=0)])

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect('/login')  # Redirect to login page
        return super(MyAdminIndexView, self).index()

# 2. Subclass MongoModelView and override scaffold_form and scaffold_filters
class ExoplanetAdminView(MongoModelView):
    column_list = ('pl_name', 'hostname', 'discoverymethod', 'disc_year', 'pl_rade', 'pl_bmasse')
    column_searchable_list = ('pl_name', 'hostname')  # Enable search

    def scaffold_form(self):
        return ExoplanetForm

    def scaffold_filters(self, name):
        """
        Manually define filters for specific fields.
        """
        if name == 'discoverymethod':
            return [self.filter_converter.convert('discoverymethod', 'Discovery Method')]
        elif name == 'disc_year':
            return [self.filter_converter.convert('disc_year', 'Discovery Year')]
        elif name == 'pl_rade':
            return [self.filter_converter.convert('pl_rade', 'Planet Radius (Earth)')]
        elif name == 'pl_bmasse':
            return [self.filter_converter.convert('pl_bmasse', 'Planet Mass (Earth)')]
        return None  # Return None for fields without filters

def init_admin(app):
    admin = Admin(app, name="ExoPlanet Admin", template_mode="bootstrap3", index_view=MyAdminIndexView())
    admin.add_view(ExoplanetAdminView(mongo.db.exoplanets, 'Exoplanets'))
