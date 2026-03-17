from agents.claim_extractor import extract_claims
from agents.retriever import retrieve
from agents.verifier import verify

text = "The government is hiding alien technology from the public."

claims = extract_claims(text)
evidence = retrieve(claims)
score = verify(claims, evidence)

print("Claims:", claims)
print("Evidence:", evidence)
print("Verification Score:", score)