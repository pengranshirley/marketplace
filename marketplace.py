import urllib
import webapp2
import jinja2
import os
import datetime


from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images
from PIL import Image

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"))


# Datastore definitions
class Persons(db.Model):
  """Models a person identified by email"""
  email = db.StringProperty()
  username = db.StringProperty()
  contact = db.StringProperty()
  registerDate = db.DateTimeProperty(auto_now_add=True)
  description = db.StringProperty(multiline=True)
  
class Items(db.Model):
  """Models an item with item_link, image_link, description, and date."""
  description = db.StringProperty(multiline=True)
  category = db.StringProperty()
  condition = db.StringProperty()
  name = db.StringProperty()
  price = db.StringProperty()
  location = db.StringProperty()
  image_link = db.StringProperty()
  img = db.BlobProperty()
  sold = db.BooleanProperty(default=False)
  date = db.DateTimeProperty(auto_now_add=True)

class Favorite(db.Model):
  productID = db.StringProperty()
  parentID = db.StringProperty()
  userID = db.StringProperty()


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
        template = jinja_environment.get_template('bazaar.html')
        self.response.out.write(template.render(template_values))
    else:
      self.redirect(self.request.host_url)

class registration(webapp2.RequestHandler):
  def get(self):
      user = users.get_current_user()
      if user:
        template_values = {
          'logout': users.create_logout_url(self.request.host_url),
        } 
        template = jinja_environment.get_template('signup.html')
        self.response.out.write(template.render(template_values))
      else:
        self.redirect(self.request.host_url)

class SellForm(webapp2.RequestHandler):
  def get(self):
      user = users.get_current_user()
      if user:
        template = jinja_environment.get_template('sell.html')
        self.response.out.write(template.render())
      else:
        self.redirect(self.request.host_url)

# Handle user registration, corresponds to "register"
class AddUser(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
         email = users.get_current_user().email()
         newPerson = Persons(key_name=email)
         newPerson.email = email
         newPerson.description = self.request.get('user_description')
         newPerson.username = self.request.get('username')
         newPerson.contact = self.request.get('contact-number')
         newPerson.put()
         #afterwards, redirect to the main page (9 categories)
         template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'username': newPerson.username,
         } 
         template = jinja_environment.get_template('bazaar.html')
         self.response.out.write(template.render(template_values))
    else:
        self.redirect(self.request.host_url)

class UserProfile(webapp2.RequestHandler):
  def get(self):
     user= users.get_current_user()
     if user:
        parent_key = db.Key.from_path('Persons', users.get_current_user().email())
        person = db.get(parent_key)


        items_onsale = db.GqlQuery("SELECT * "
                                   "FROM Items "
                                   "WHERE sold = False AND ANCESTOR IS :1 "
                                   "ORDER BY date DESC",
                                   parent_key)


        items_sold =   db.GqlQuery("SELECT * "
                                   "FROM Items "
                                   "WHERE sold = True AND ANCESTOR IS :1 "
                                   "ORDER BY date DESC",
                                   parent_key)
        
        template_values = {
            'user': person,
            'logout': users.create_logout_url(self.request.host_url),
            'items_onsale': items_onsale,
            "items_sold": items_sold,
            
        } 
        template = jinja_environment.get_template('profile.html')
        self.response.out.write(template.render(template_values))

     else:
        self.redirect(self.request.host_url)


class AddItem(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
        parent_key = db.Key.from_path('Persons', users.get_current_user().email())
        person = db.get(parent_key)
        item = Items(parent=parent_key)
        item.description = self.request.get('desc')
        item.category = self.request.get("item_category")
        item.condition = self.request.get("item_condition")
        item.name = self.request.get("item_name")
        item.location = self.request.get("item_location")
        item.price = self.request.get('item_price')
        # didn't check whether it's indeed an image
        picture = self.request.get('img')
        if picture:
               item.img = db.Blob(images.resize(picture, 360))
        item.put()
        fav = 0
        self.redirect("/viewProduct?ID="+str(item.key().id())+"&user="+user.email())
        """
        template_values = {
              'user_mail': users.get_current_user().email(),
              'logout': users.create_logout_url(self.request.host_url),
              'item': item,
              'fav': fav,
              'owner': person,
        } 
        template = jinja_environment.get_template('product.html')
        self.response.out.write(template.render(template_values))
        """
    else:
        self.redirect(self.request.host_url)

class SoldCondition(webapp2.RequestHandler):
  def get(self, name):
    user = users.get_current_user()
    if user:
      key = self.request.get("ID")  #id is each product's natural primary key
      parent_email = self.request.get("user")
      person = db.Key.from_path('Persons', parent_email)
      item = Items.get_by_id(int(key), parent = person)
      if item.sold == True:
        item.sold = False
        item.put()
      else:
        item.sold = True
        item.put()
      self.redirect("/profile")

    else:
      self.redirect(self.request.host_url)

class RemoveFavorite(webapp2.RequestHandler):
  def get(self, name):
    user = users.get_current_user()
    if user:
      key = self.request.get("ID")  
      parent_email = self.request.get("user")
      current_user = user.email()


      query = db.GqlQuery("SELECT * "
                          "FROM Favorite "
                          "WHERE productID = :1 AND parentID = :2 AND userID = :3",
                          key, parent_email, current_user)

      for p in query:
        p.delete()

     # self.redirect("/viewProduct?ID="+key+"&user="+parent_email)

    else:
      self.redirect(self.request.host_url)


class AddFavorite(webapp2.RequestHandler):
  def get(self, name):
    user = users.get_current_user()
    if user:
      key = self.request.get("ID")  #id is each product's natural primary key
      parent_email = self.request.get("user")
      current_user = user.email()
      favorite = Favorite()
      favorite.productID = key
      favorite.parentID = parent_email
      favorite.userID = current_user
      favorite.put()
      #self.redirect("/viewProduct?ID="+key+"&user="+parent_email)

    else:
      self.redirect(self.request.host_url)

class ViewFavorite(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
        query = db.GqlQuery("SELECT * "
                            "FROM Favorite "
                            "WHERE userID = :1",
                            user.email())

        template_values = {
              'user_mail': users.get_current_user().email(),
              'logout': users.create_logout_url(self.request.host_url),
              'items': query,
        } 
        template = jinja_environment.get_template('favorite.html')
        self.response.out.write(template.render(template_values)) 

    else:
      self.redirect(self.request.host_url)





class ViewImage(webapp2.RequestHandler):
  def get(self, name):
      key = self.request.get("ID")  
      parent_email = self.request.get("user")
      person = db.Key.from_path('Persons', parent_email)
      item = Items.get_by_id(int(key), parent = person)
      img = item.img
      if img:
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(img)
      else:
        self.redirect("http://www.placehold.it/360x240/EFEFEF/AAAAAA&text=no+image")


class DisplayByC(webapp2.RequestHandler):
  def get(self, name):
        category = self.request.get("c")
        page = self.request.get("p") 
        start_no = int((int(page)-1)*4)
        query = db.GqlQuery("SELECT * "
                            "FROM Items "
                            "WHERE sold = False AND category = :1 "
                            "ORDER BY date DESC",
                            category)
    
        query_2 = query.fetch(4, int(start_no))
        if query_2:
          template_values = {
            'user_mail': users.get_current_user().email(),
            'logout': users.create_logout_url(self.request.host_url),
            'category': category,
            'page': page,
            'items': query_2,
          }
          if start_no == 0:
            template = jinja_environment.get_template('category.html')
          else:
            template = jinja_environment.get_template('category_append.html')
          self.response.out.write(template.render(template_values)) 
          #Assume page no is always valid
          #Suppose one page display 9 products
          #Return all 9 items

class DisplayProduct(webapp2.RequestHandler):
  def get(self, name):
    user = users.get_current_user()
    if user:
      key = self.request.get("ID")  
      parent_email = self.request.get("user")
      person = db.Key.from_path('Persons', parent_email)
      current_user = user.email()
      item = Items.get_by_id(int(key), parent = person)

      query = db.GqlQuery("SELECT * "
                          "FROM Favorite "
                          "WHERE productID = :1 AND parentID = :2 AND userID = :3",
                          key, parent_email, current_user)
      query_2 = query.get()

      if query_2:
        fav = 1
      else:
        fav = 0

      template_values = {
        'user_mail': users.get_current_user().email(),
        'logout': users.create_logout_url(self.request.host_url),
        'item': item,
        'owner':person,
        'fav_status': fav, # 1 stands for alrday favorite, 0 stands for not
      }
      template = jinja_environment.get_template('product.html')
      self.response.out.write(template.render(template_values))
    else:
      self.redirect(self.request.host_url)

app = webapp2.WSGIApplication([('/bazaar', MainPage),
                               ('/signup',registration),
                               ('/register', AddUser),
                               ('/profile', UserProfile),
                               ('/new', SellForm),
                               ('/create', AddItem),
                               ('/favorite', ViewFavorite),
                               (r'/viewCategory(.*)', DisplayByC),
                               (r'/img(.*)', ViewImage),
                               (r'/addFavorite(.*)', AddFavorite),
                               (r'/unfavorite(.*)', RemoveFavorite),
                               (r'/sellProduct(.*)', SoldCondition),
                               (r'/viewProduct(.*)', DisplayProduct)],
                              debug=True)
