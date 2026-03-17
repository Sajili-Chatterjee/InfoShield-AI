from agents.claim_extractor import extract_claims

text = """
The government is hiding alien technology. Scientists deny this claim.
Many reports suggest misinformation spreads quickly online.
"""

claims = extract_claims(text)

print(claims)