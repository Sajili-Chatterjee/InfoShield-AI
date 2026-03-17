from models.predictor import predict
from agents.claim_extractor import extract_claims
from agents.retriever import retrieve
from agents.verifier import verify
from agents.scorer import compute_final_score, get_final_label

text = "The government is hiding alien technology from the public."

model_output = predict(text)
claims = extract_claims(text)
evidence = retrieve(claims)
verification_score = verify(claims, evidence)

final_score = compute_final_score(model_output, verification_score, evidence)
final_label = get_final_label(final_score)

print("Model:", model_output)
print("Verification:", verification_score)
print("Evidence:", evidence)
print("Final Score:", final_score)
print("Final Label:", final_label)