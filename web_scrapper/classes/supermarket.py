class WorkingHour:
    def __init__(self, start, end):
        self.start = start
        self.end = end

class WeekWorkingHours:
    #If variable is none the supermarket does not open on that day
    def __init__(self):
        self.Monday = None
        self.Tuesday = None
        self.Wednesday = None
        self.Thursday = None
        self.Friday = None
        self.Saturday = None
        self.Sunday = None

class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
        self.description = None
        
    def display_info(self):
        print('- Product Info -')
        print('Name: ', self.name)
        print('Price: ', self.price)
        print('Description: ', self.description)
        
class Supermarket:
    def __init__(self, url):
        self.name = None
        self.url = url
        self.address = None
        self.zip_code = None
        self.cnpj = None #Won't be able to be retrieved in all sources
        self.working_hours = WeekWorkingHours()
        self.delivery_days = []
        self.delivery_price = None
        self.grab_delivery = False
        self.products = []
    
    def display_info(self):
        print('- Supermarket Info -')
        print('Name: ', self.name)
        print('Url: ', self.url)
        print('Address: ', self.address)
        print('ZIP: ', self.zip_code)
        print('CNPJ: ', self.cnpj)
        print('Working Hours: ')
        for day, hours in self.working_hours.__dict__.items():
            if(hours == None):
                print(f"    {day}: Does not open")
            else:
                print(f"    {day}: {hours.start} - {hours.end}")
        print('Delivery Day: ', self.delivery_days)
        print('Delivery Price: ', self.delivery_price)
        print('Grab Delivery: ', self.grab_delivery)
        print('Num of Products: ', len(self.products))