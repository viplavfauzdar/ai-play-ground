import streamlit as st
import requests

st.title("Mock Review Response UI")

reviews = requests.get("http://localhost:8000/api/reviews").json()["reviews"]

business_type = st.text_input("Business Type", value="restaurant")

for r in reviews:
    st.subheader(f"⭐ {r['starRating']} — {r['reviewer']['displayName']}")
    st.write(r['comment'])
    if "reviewReply" in r:
        st.success(f"Response: {r['reviewReply']['comment']}")
    else:
        if st.button("Generate AI Reply", key=r['reviewId']):
            payload = {
                "review_id": r['reviewId'],
                "review": r['comment'],
                "business_type": business_type
            }
            res = requests.post("http://localhost:8000/api/reply", json=payload)
            raw_reply = res.json().get("reply", "")
            reply_text = raw_reply.get("text") if isinstance(raw_reply, dict) else raw_reply
            st.success(f"Response: {reply_text}")