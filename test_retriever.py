from agents.claim_extractor import extract_claims
from agents.retriever import retrieve

text = "The government is hiding alien technology from the public."

claims = extract_claims(text)
evidence = retrieve(claims)

print("Claims:", claims)
print("Evidence:", evidence)