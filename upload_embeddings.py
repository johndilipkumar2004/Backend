import pickle
from dotenv import dotenv_values
from supabase import create_client

config = dotenv_values(".env")

supabase = create_client(config["SUPABASE_URL"], config["SUPABASE_ANON_KEY"])

# Load local encodings
data = pickle.load(open('dataset/encodings.pkl', 'rb'))

encodings = data['encodings']
student_ids = data['student_ids']

print(f"Total encodings: {len(encodings)}")

# Upload each embedding
success = 0
for i, (embedding, student_id) in enumerate(zip(encodings, student_ids)):
    try:
        supabase.table("face_embeddings").insert({
            "student_id": student_id,
            "embedding": embedding.tolist()
        }).execute()
        success += 1
        print(f"✅ Uploaded {i+1}/{len(encodings)} - student: {student_id}")
    except Exception as e:
        print(f"❌ Failed {i+1}: {e}")

print(f"\nDone! {success}/{len(encodings)} uploaded successfully.")