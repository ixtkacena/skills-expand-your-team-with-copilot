"""
In-memory database configuration and setup for Mergington High School API
"""

from argon2 import PasswordHasher

# In-memory storage
activities_db = {}
teachers_db = {}

# Simple in-memory collection classes to mimic MongoDB interface
class InMemoryCollection:
    def __init__(self, data_store):
        self.data_store = data_store
    
    def find(self, query=None):
        """Find documents matching query"""
        if query is None or query == {}:
            return [{"_id": key, **value} for key, value in self.data_store.items()]
        
        results = []
        for key, value in self.data_store.items():
            if self._matches_query({"_id": key, **value}, query):
                results.append({"_id": key, **value})
        return results
    
    def find_one(self, query):
        """Find single document"""
        if "_id" in query:
            key = query["_id"]
            if key in self.data_store:
                return {"_id": key, **self.data_store[key]}
            return None
        return None
    
    def insert_one(self, document):
        """Insert a document"""
        doc_id = document["_id"]
        doc_data = {k: v for k, v in document.items() if k != "_id"}
        self.data_store[doc_id] = doc_data
        return True
    
    def update_one(self, query, update):
        """Update a document"""
        if "_id" in query:
            key = query["_id"]
            if key in self.data_store:
                if "$push" in update:
                    for field, value in update["$push"].items():
                        if field not in self.data_store[key]:
                            self.data_store[key][field] = []
                        self.data_store[key][field].append(value)
                if "$pull" in update:
                    for field, value in update["$pull"].items():
                        if field in self.data_store[key]:
                            if value in self.data_store[key][field]:
                                self.data_store[key][field].remove(value)
                return type('obj', (object,), {'modified_count': 1})
        return type('obj', (object,), {'modified_count': 0})
    
    def count_documents(self, query):
        """Count documents"""
        return len(self.data_store)
    
    def aggregate(self, pipeline):
        """Simple aggregation for getting unique days"""
        if pipeline and pipeline[0].get("$unwind") == "$schedule_details.days":
            all_days = set()
            for activity in self.data_store.values():
                if "schedule_details" in activity and "days" in activity["schedule_details"]:
                    all_days.update(activity["schedule_details"]["days"])
            return [{"_id": day} for day in sorted(all_days)]
        return []
    
    def _matches_query(self, doc, query):
        """Check if document matches query"""
        for key, condition in query.items():
            if key == "schedule_details.days":
                if "$in" in condition:
                    doc_days = doc.get("schedule_details", {}).get("days", [])
                    if not any(day in doc_days for day in condition["$in"]):
                        return False
                continue
            elif key == "schedule_details.start_time":
                if "$gte" in condition:
                    doc_time = doc.get("schedule_details", {}).get("start_time", "")
                    if doc_time < condition["$gte"]:
                        return False
                continue
            elif key == "schedule_details.end_time":
                if "$lte" in condition:
                    doc_time = doc.get("schedule_details", {}).get("end_time", "")
                    if doc_time > condition["$lte"]:
                        return False
                continue
            elif key == "difficulty_level":
                if isinstance(condition, dict) and "$exists" in condition:
                    # Handle $exists operator
                    field_exists = key in doc and doc[key] is not None
                    if condition["$exists"] != field_exists:
                        return False
                elif doc.get("difficulty_level") != condition:
                    return False
                continue
        return True

# Initialize collections
activities_collection = InMemoryCollection(activities_db)
teachers_collection = InMemoryCollection(teachers_db)

# Methods
def hash_password(password):
    """Hash password using Argon2"""
    ph = PasswordHasher()
    return ph.hash(password)

def init_database():
    """Initialize database if empty"""

    # Initialize activities if empty
    if activities_collection.count_documents({}) == 0:
        for name, details in initial_activities.items():
            activities_collection.insert_one({"_id": name, **details})
            
    # Initialize teacher accounts if empty
    if teachers_collection.count_documents({}) == 0:
        for teacher in initial_teachers:
            teachers_collection.insert_one({"_id": teacher["username"], **teacher})

# Initial database if empty
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
        "schedule_details": {
            "days": ["Monday", "Friday"],
            "start_time": "15:15",
            "end_time": "16:45"
        },
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
        "difficulty_level": "Beginner"
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 7:00 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "07:00",
            "end_time": "08:00"
        },
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
        "difficulty_level": "Intermediate"
    },
    "Morning Fitness": {
        "description": "Early morning physical training and exercises",
        "schedule": "Mondays, Wednesdays, Fridays, 6:30 AM - 7:45 AM",
        "schedule_details": {
            "days": ["Monday", "Wednesday", "Friday"],
            "start_time": "06:30",
            "end_time": "07:45"
        },
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and compete in basketball tournaments",
        "schedule": "Wednesdays and Fridays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Wednesday", "Friday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore various art techniques and create masterpieces",
        "schedule": "Thursdays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Thursday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
        "difficulty_level": "Beginner"
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Monday", "Wednesday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and prepare for math competitions",
        "schedule": "Tuesdays, 7:15 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "07:15",
            "end_time": "08:00"
        },
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
        "difficulty_level": "Advanced"
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Friday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "amelia@mergington.edu"],
        "difficulty_level": "Intermediate"
    },
    "Weekend Robotics Workshop": {
        "description": "Build and program robots in our state-of-the-art workshop",
        "schedule": "Saturdays, 10:00 AM - 2:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "10:00",
            "end_time": "14:00"
        },
        "max_participants": 15,
        "participants": ["ethan@mergington.edu", "oliver@mergington.edu"],
        "difficulty_level": "Advanced"
    },
    "Science Olympiad": {
        "description": "Weekend science competition preparation for regional and state events",
        "schedule": "Saturdays, 1:00 PM - 4:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "13:00",
            "end_time": "16:00"
        },
        "max_participants": 18,
        "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
    },
    "Sunday Chess Tournament": {
        "description": "Weekly tournament for serious chess players with rankings",
        "schedule": "Sundays, 2:00 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Sunday"],
            "start_time": "14:00",
            "end_time": "17:00"
        },
        "max_participants": 16,
        "participants": ["william@mergington.edu", "jacob@mergington.edu"],
        "difficulty_level": "Advanced"
    },
    "Manga Maniacs": {
        "description": "Dive into epic adventures, discover incredible powers, and connect with unforgettable heroes! Join fellow manga enthusiasts as we explore everything from shonen battles to slice-of-life stories. Whether you're rooting for Naruto, One Piece, or love discovering hidden gems, this is your otaku home base!",
        "schedule": "Tuesdays, 7:00 PM - 8:00 PM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "19:00",
            "end_time": "20:00"
        },
        "max_participants": 15,
        "participants": []
    }
}

initial_teachers = [
    {
        "username": "mrodriguez",
        "display_name": "Ms. Rodriguez",
        "password": hash_password("art123"),
        "role": "teacher"
     },
    {
        "username": "mchen",
        "display_name": "Mr. Chen",
        "password": hash_password("chess456"),
        "role": "teacher"
    },
    {
        "username": "principal",
        "display_name": "Principal Martinez",
        "password": hash_password("admin789"),
        "role": "admin"
    }
]

