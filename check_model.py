import pickle

with open('models\\model.pkl', 'rb') as f:
    model = pickle.load(f)
    
print(f"Model expects {model.n_features_in_} features")