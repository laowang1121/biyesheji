from app import app
from backend.models import db
from backend.algorithm.recommender import ConfigRecommender

def test():
    with app.app_context():
        rec = ConfigRecommender(budget=5000, mode='gaming')
        res = rec.recommend()
        print(f"Budget: {res['total_budget']}")
        print(f"Total Price: {res['total_price']}")
        print(f"Budget Usage: {res['budget_usage']}%")

if __name__ == "__main__":
    test()
