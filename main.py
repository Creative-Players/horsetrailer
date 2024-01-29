import spacy
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report

# Load SpaCy English model
nlp = spacy.load("en_core_web_sm")

# Example labeled data
data = [
    ("What is the best way to cook a steak?", 1),
    ("How long does it take to bake a cake?", 1),
    ("Can you recommend a good pasta recipe?", 1),
    ("What are some healthy vegetarian dishes?", 1),
    ("How do I make homemade pizza?", 1),
    ("What ingredients do I need for a Caesar salad?", 1),
    ("Is there an easy recipe for apple pie?", 1),
    ("How can I make gluten-free bread?", 1),
    ("What's the secret to a fluffy omelette?", 1),
    ("Are there any quick stir-fry recipes?", 1),
    ("How do you prepare a vegan curry?", 1),
    ("What is the best way to grill fish?", 1),
    ("Can you suggest a good burger joint?", 1),
    ("What are some traditional Japanese dishes?", 1),
    ("How do I make a smoothie bowl?", 1),
    ("What's the recipe for classic French onion soup?", 1),
    ("How can I make a mojito cocktail?", 1),
    ("What are some easy microwave meals?", 1),
    ("How do you bake a sweet potato?", 1),
    ("Can you freeze homemade lasagna?", 1),
    ("What's a good recipe for chicken marsala?", 1),
    ("How do I make a chocolate chip cookie?", 1),
    ("What are some low-carb meal options?", 1),
    ("How do you make a strawberry shortcake?", 1),
    ("What's the best way to cook rice?", 1),
    ("What's the weather like today?", 0),
    ("Can you recommend a good book?", 0),
    ("How do I change a car tire?", 0),
    ("What are the best exercises for abs?", 0),
    ("How can I improve my Wi-Fi speed?", 0),
    ("What are some effective study techniques?", 0),
    ("Can you suggest a good Netflix series?", 0),
    ("How do I fix a leaky faucet?", 0),
    ("What's the latest iPhone model?", 0),
    ("How can I learn to play the guitar?", 0),
    ("What are the symptoms of a cold?", 0),
    ("How do you change a lightbulb?", 0),
    ("What's the best way to learn a new language?", 0),
    ("How do I reset my password?", 0),
    ("Can you suggest a good workout routine?", 0),
    ("How can I decorate my living room?", 0),
    ("What are the best plants for indoors?", 0),
    ("How do I backup my computer?", 0),
    ("What are some tips for job interviews?", 0),
    ("How can I improve my credit score?", 0),
    ("What's the best way to clean windows?", 0),
    ("How do I book a flight online?", 0),
    ("What are some fun board games?", 0),
    ("How can I meditate effectively?", 0),
    ("What's the best way to take notes?", 0),
    # ... add more data as needed
]


# Preprocess with SpaCy
def preprocess_text(text):
    doc = nlp(text)
    processed_tokens = []
    for token in doc:
        # Keep the original text for specific words, even if they are stop words
        if token.text.lower() in ['what', 'how', 'why', 'when', 'do', 'a', 'you']:
            processed_tokens.append(token.text)
        # For other tokens, lemmatize and exclude stop words and punctuation
        elif not token.is_stop and not token.is_punct:
            processed_tokens.append(token.lemma_)
    return " ".join(processed_tokens)

preprocessed_data = [(preprocess_text(text), label) for text, label in data]
sentences, labels = zip(*preprocessed_data)

# Splitting the data
X_train, X_test, y_train, y_test = train_test_split(sentences, labels, test_size=0.2)

# Vectorizing the text
vectorizer = TfidfVectorizer()
X_train_tfidf = vectorizer.fit_transform(X_train)

# Training a Naive Bayes classifier
clf = MultinomialNB().fit(X_train_tfidf, y_train)

# Transform test data and predict
X_test_tfidf = vectorizer.transform(X_test)
predictions = clf.predict(X_test_tfidf)

# Evaluate the model
print(classification_report(y_test, predictions, zero_division=1))

# Function to segment text into sentences and preprocess each sentence
def segment_and_preprocess(text):
    doc = nlp(text)
    return [preprocess_text(sent.text) for sent in doc.sents]

# Classifying new text with multiple sentences
new_texts = [
    "What time is the movie tonight? SpaCy is one of the most versatile open source NLP libraries.",
    "Do you have a recipe for lasagna? SpaCy also provides pre-trained word vectors."
]

for text in new_texts:
    segmented_sentences = segment_and_preprocess(text)
    sentences_tfidf = vectorizer.transform(segmented_sentences)
    sentences_predictions = clf.predict(sentences_tfidf)

    for sentence, pred in zip(segmented_sentences, sentences_predictions):
        print(f"Sentence: {sentence}, Food-related: {'Yes' if pred == 1 else 'No'}")
