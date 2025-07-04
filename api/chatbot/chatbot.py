import os
from openai import OpenAI

# Load OpenAI API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Raise an error if it's missing
if not api_key:
    raise ValueError("OPENAI_API_KEY is missing! Make sure it’s set in Vercel.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def generate_linkedin_reply(comment, context="professional"):
    try:
        prompt = f"""
        You are a professional AI Solutions Architect specializing in building custom AI tools.
        Read the LinkedIn comment and write a concise, friendly, and insightful reply.
        Acknowledge the insight, offer value, and subtly mention your AI expertise.

        Comment: {comment}
        Tone: {context}
        """
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional LinkedIn assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        raise Exception(f"Failed to generate reply: {str(e)}")
