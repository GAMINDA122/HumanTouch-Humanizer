import random
import re
import spacy
from flask import Flask, request, jsonify, render_template
import requests
from sentence_transformers import SentenceTransformer, util
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

embedder = SentenceTransformer('all-MiniLM-L6-v2')
nlp = spacy.load("en_core_web_sm")

# Configure Gemini API
API_KEY = os.getenv("API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Word simplification dictionary
word_simplifier = {
    "utilize": "use", "commence": "start", "terminate": "end", "numerous": "many",
    "assist": "help", "demonstrate": "show", "contemplate": "think about", "methodology": "method",
    "consequently": "so", "approximately": "about", "therefore": "so", "ameliorate": "improve",
    "facilitate": "help", "implement": "do", "acquire": "get", "endeavor": "try", "prioritize": "focus on",
    "subsequent": "next", "predominantly": "mainly", "optimize": "improve", "utilization": "use",
    "collaborate": "work together", "comprehensive": "detailed", "infrastructure": "framework",
    "sufficient": "enough", "innovative": "new", "predicament": "problem", "concur": "agree",
    "adverse": "bad", "exemplify": "show", "cognizant": "aware"
}

# Contractions
contractions = {
    r"\bis not\b": "isn't", r"\bare not\b": "aren't", r"\bdoes not\b": "doesn't", r"\bdid not\b": "didn't",
    r"\bcan not\b": "can't", r"\bcannot\b": "can't", r"\bwill not\b": "won't", r"\bwould not\b": "wouldn't",
    r"\bshould not\b": "shouldn't", r"\bhave not\b": "haven't", r"\bhas not\b": "hasn't", r"\bhad not\b": "hadn't",
    r"\bI am\b": "I'm", r"\bwe are\b": "we're", r"\bthey are\b": "they're", r"\byou are\b": "you're",
    r"\bI will\b": "I'll", r"\bwe will\b": "we'll", r"\bthey will\b": "they'll", r"\byou will\b": "you'll"
}

# === Processing Functions ===

def inject_fillers(text):
    return text  # removed filler insertion

def inject_discourse_markers(text):
    return text  # removed discourse markers

def inject_typos_and_mistakes(text):
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < 0.005:  # bump typo chance
            action = random.choice(['comma', 'period', 'typo', 'capitalize', 'ellipsis', 'dash', 'repeat'])
            if action == 'comma':
                chars[i] = ','
            elif action == 'period':
                chars[i] = '.'
            elif action == 'typo' and chars[i].isalpha():
                chars[i] = random.choice('abcdefghijklmnopqrstuvwxyz')
            elif action == 'capitalize':
                chars[i] = chars[i].upper() if random.random() < 0.5 else chars[i].lower()
            elif action == 'ellipsis' and i + 2 < len(chars):
                chars[i:i+3] = ['.', '.', '.']
            elif action == 'dash':
                chars[i] = '-'
            elif action == 'repeat' and i + 1 < len(chars) and chars[i].isalpha():
                chars.insert(i, chars[i])
    return ''.join(chars)

def shuffle_words_small_chunks(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    new_sentences = []
    for sent in sentences:
        words = sent.split()
        if len(words) > 6 and random.random() < 0.25:
            chunk_size = random.randint(2, min(5, len(words)//2))
            start_idx = random.randint(0, len(words) - chunk_size)
            chunk = words[start_idx:start_idx+chunk_size]
            random.shuffle(chunk)
            words[start_idx:start_idx+chunk_size] = chunk
            sent = ' '.join(words)
        new_sentences.append(sent)
    return ' '.join(new_sentences)

def repeat_words_randomly(text):
    words = text.split()
    new_words = []
    for w in words:
        new_words.append(w)
        if random.random()< 0.03:
            new_words.append(w)
    return ' '.join(new_words)

def vary_sentence_length(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    result = []
    for s in sentences:
        if result and random.random() < 0.6:
            sep = random.choice([', ', ' - '])
            result[-1] = result[-1].rstrip('.!?') + sep + s[0].lower() + s[1:]
        else:
            result.append(s)
    return ' '.join(result)

def drop_small_function_words(text):
    pattern = r'\b(the|a|an|that|which|and)\b'
    def replacer(match):
        return '' if random.random() < 0.1 else match.group(0)
    return re.sub(pattern, replacer, text, flags=re.IGNORECASE)

def simplify_text(text):
    for complex_word, simple_word in word_simplifier.items():
        text = re.sub(r'\b' + re.escape(complex_word) + r'\b', simple_word, text, flags=re.IGNORECASE)
    return text

def apply_contractions(text):
    for phrase, contraction in contractions.items():
        text = re.sub(phrase, contraction, text, flags=re.IGNORECASE)
    return text

def remove_subheadings(text):
    lines = text.split('\n')
    return "\n".join([line for line in lines if re.match(r'^#{1,2} ', line) or not re.match(r'^#{3,} ', line)])

def remove_equations_and_graphs(text):
    text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)
    text = re.sub(r'\$.*?\$', '', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    return text

def spacy_human_touch(text):
    doc = nlp(text)
    new_text = []
    for sent in doc.sents:
        tokens = []
        for token in sent:
            if token.ent_type_ == "ORG":
                tokens.append("")
            elif token.ent_type_ == "DATE":
                tokens.append("some time ago")
            elif token.lemma_ == "increase" and token.pos_ == "VERB":
                tokens.append("grow")
            else:
                tokens.append(token.text)
        new_text.append(" ".join(tokens))
    return " ".join(new_text)

def postprocess(text):
    text = remove_subheadings(text)
    text = simplify_text(text)
    text = apply_contractions(text)
    text = drop_small_function_words(text)
    # fillers and discourse_markers removed
    text = repeat_words_randomly(text)
    text = shuffle_words_small_chunks(text)
    text = vary_sentence_length(text)
    text = spacy_human_touch(text)
    text = inject_typos_and_mistakes(text)

    # === New rules applied here ===
    text = text.lstrip(' )([]!,')
    if text:
        text = text[0].upper() + text[1:]

    sentences = re.split('([.!?] +)', text)
    text = ''.join(s.capitalize() if i % 2 == 0 else s for i, s in enumerate(sentences))
    return text.strip()

def chunk_text(text, max_words=2000):
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def count_words(text):
    return len(re.findall(r'\b\w+\b', text))

def split_paragraphs(text):
    return [p.strip() for p in text.strip().split('\n') if p.strip()]

# === Routes ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/humanize', methods=['POST'])
def humanize():
    data = request.get_json()
    ai_text = data.get('text', '')
    cleaned_text = remove_equations_and_graphs(ai_text)

    chunks = chunk_text(cleaned_text, max_words=2000)

    try:
        humanized_chunks = []

        for chunk in chunks:
            prompt = f"""
                    You are an expert at rewriting text naturally and fluently while keeping the original paragraph structure.

                    TASK:
                    - Rewrite each paragraph so it sounds smooth and human-like, like a university student or blogger.
                    - Keep each rewritten paragraph about the same length as the original.
                    - Do NOT merge, split, or remove paragraphs. The output must have the same number of paragraphs as the input.
                    - Separate paragraphs with exactly two newline characters (\\n\\n).
                    - *Do not add filler or unnecessary content (like paragraph 1 ,here 's the rewritten text : , etc)*.

                    RULES:
                    - Do not start any paragraph with interjections like "Oh" or "Ah".
                    - Output ONLY the rewritten text — no explanations or original text.
                    - Keep the original meaning.
                    - Retain 70%–85% of the original words.
                    - Ensure each rewritten paragraph’s total word count is at least 20 words more OR less than the original.
                    - If the input has no headings, do not add any.
                    - If the input has headings, keep them exactly.
                    - Do not use "),(,],[,!" in output.
                    - Start output only with a letter (A-Z,a-z).

                    INPUT:
                    {chunk}
                    """
            
            # Use Gemini API instead of Ollama
            response = model.generate_content(prompt)
            raw_humanized = response.text.strip()

            final_output = postprocess(raw_humanized)

            original_wc = count_words(chunk)
            humanized_wc = count_words(final_output)
            diff = humanized_wc - original_wc

            if abs(diff) > 20:
                if diff > 20:
                    sentences = re.split(r'(?<=[.!?]) +', final_output)
                    while count_words(' '.join(sentences)) - original_wc > 20 and sentences:
                        sentences.pop()
                    final_output = ' '.join(sentences)
                elif diff < -20:
                    final_output += ' '  

            humanized_chunks.append(final_output.strip())

        final_text = '\n\n'.join(humanized_chunks)

        embeddings = embedder.encode([cleaned_text, final_text], convert_to_tensor=True)
        cosine_score = util.cos_sim(embeddings[0], embeddings[1]).item()

        original_word_count = count_words(cleaned_text)
        humanized_word_count = count_words(final_text)
        word_retention = (humanized_word_count / original_word_count) * 100

        print(f"\nOriginal words: {original_word_count}")
        print(f"Humanized words: {humanized_word_count}")
        print(f"Word retention: {word_retention:.2f}%")
        print(f"Cosine Similarity: {cosine_score:.4f}")

        return jsonify({'humanized': final_text, 'similarity': cosine_score})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)