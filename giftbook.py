import urllib
import webapp2
import jinja2
import os
import datetime


from google.appengine.ext import db
from google.appengine.api import users

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"))



# Datastore definitions
class Persons(db.Model):
  """Models a person identified by email"""
  email = db.StringProperty()
  username = db.StringProperty()
  registerDate = db.DateTimeProperty(auto_now_add=True)
  description = db.StringProperty(multiline=True)
  
class Items(db.Model):
  """Models an item with item_link, image_link, description, and date."""
  description = db.StringProperty(multiline=True)
  category = db.StringProperty()
  condition = db.StringProperty()
  name = db.StringProperty()
  location = db.StringProperty()
  image_link = db.StringProperty()
  img = db.BlobProperty()
  sold = db.BooleanProperty(default=False)
  date = db.DateTimeProperty(auto_now_add=True)

# This part for the front page
# Process: User login --> First time user diverts to register pages
#                     --> Non first time user diverts to "category.html"/ displayProductsByCategory
class MainPage(webapp2.RequestHandler):
  """ Front page for those logged in """
  def get(self):
    user = users.get_current_user()
    if user:  # signed in already
      parent_key = db.Key.from_path('Persons', users.get_current_user().email())
      person = db.get(parent_key)
      # For first time user, divert to register page
      if person == None:
        self.redirect('/signup')
      # For non-first time user, divert to "display by category"
      else:
        template_values = {
          'username': person.username,
          'user_mail': users.get_current_user().email(),
          'logout': users.create_logout_url(self.request.host_url),
        } 
        template = jinja_environment.get_template('frontuser.html')
        self.response.out.write(template.render(template_values))
    else:
      self.redirect(self.request.host_url)

class registration(webapp2.RequestHandler):
  def get(self):
      template = jinja_environment.get_template('signup.html')
      self.response.out.write(template.render())

class SellForm(webapp2.RequestHandler):
  def get(self):
      template = jinja_environment.get_template('sell.html')
      self.response.out.write(template.render())


# Handle user registration, corresponds to "register"
class AddUser(webapp2.RequestHandler):
  def post(self):
    email = users.get_current_user().email()
    newPerson = Persons(key_name=email)
    newPerson.email = email
    newPerson.description = self.request.get('user_description')
    newPerson.username = self.request.get('username')
    newPerson.put()
    #afterwards, redirect to the main page (9 categories)
    template_values = {
          'user_mail': users.get_current_user().email(),
          'logout': users.create_logout_url(self.request.host_url),
          'username': newPerson.username,
    } 
    template = jinja_environment.get_template('frontuser.html')
    self.response.out.write(template.render(template_values))


class AddItem(webapp2.RequestHandler):
  def post(self):
    parent_key = db.Key.from_path('Persons', users.get_current_user().email())
    person = db.get(parent_key)
    item = Items(parent=parent_key)
    item.description = self.request.get('desc')
    item.category = self.request.get("item_category")
    item.condition = self.request.get("item_condition")
    item.name = self.request.get("item_name")
    item.location = self.request.get("item_location")
    item.image_link = self.request.get('image_url')
    item.put()

    template_values = {
          'user_mail': users.get_current_user().email(),
          'logout': users.create_logout_url(self.request.host_url),
          'item': item,
          'owner': person,
    } 
    template = jinja_environment.get_template('product.html')
    self.response.out.write(template.render(template_values))


    #img = db.BlobProperty() hasn't implemented yet
    #divert to product display page
    """
    self.redirect('/viewProduct?ID='+item.Key().id()+"user="+parent_key)
    """
  

class DisplayByC(webapp2.RequestHandler):
  def get(self, name):
    
    category = self.request.get("c")
    page = self.request.get("p")
    
    start_no = (int(page)-1)*9
    query = db.GqlQuery("SELECT * " +
                        "FROM Items " +
                        "ORDER BY date DESC" +
                        "LIMIT 9" +
                        "OFFSET :1" +
                        "WHERE category = :2", start_no, category)
    


    template_values = {
      'user_mail': users.get_current_user().email(),
      'logout': users.create_logout_url(self.request.host_url),
      'category': category,
      'page': page,
      'items': query,
    }
    template = jinja_environment.get_template('category.html')
    self.response.out.write(template.render(template_values)) 
    
    #Assume page no is always valid
    #Suppose one page display 9 products
    #Return all 9 items

class DisplayProduct(webapp2.RequestHandler):
  def get(self):
    key = self.request.get("ID")  #id is each product's natural primary key
    parent = self.request.get("user")
    person = db.get(parent_key)
    item = Items.get_by_id(key, parent = person)
    template_values = {
      'user_mail': users.get_current_user().email(),
      'logout': users.create_logout_url(self.request.host_url),
      'item': item,
      'owner':person,
    }
    template = jinja_environment.get_template('product.html')
    self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([('/login', MainPage),
                               ('/signup',registration),
                               ('/register', AddUser),
                               ('/sell', SellForm),
                               ('/create', AddItem),
                               (r'/viewCategory(.*)', DisplayByC),
                               (r'/viewProduct(.*)', DisplayProduct)],
                              debug=True)
