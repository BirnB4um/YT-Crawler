# from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import fasttext
import numpy as np
import os

from Singleton import SingletonMeta
from logger import CrawlLogger
logger = CrawlLogger().logger


class Models(metaclass=SingletonMeta):

    def __init__(self, base_path="/opt/yt-crawler/models/"):
        self.base_path = base_path
        self.language_model = None
        self.music_model = None
        self.emb_model = None

        self.load_models()

    def load_models(self):
        try:
            self.language_model = fasttext.load_model(os.path.join(self.base_path, "lid.176.ftz"))
        except Exception as e:
            logger.error(f"Models: Error loading fasttext model: {str(e)}")
            raise e

        # try:
        #     self.music_model = pipeline("zero-shot-classification", model="typeform/mobilebert-uncased-mnli")
        # except Exception as e:
        #     logger.error(f"Models: Error loading music model: {str(e)}")
        #     raise e

        try:
            self.emb_model = SentenceTransformer(os.path.join(self.base_path, "paraphrase-multilingual-MiniLM-L12-v2"))
            self.emb_dims = self.emb_model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Models: Error loading embedding model: {str(e)}")
            raise e
        
        
    def predict_language(self, text):
        lang, prob = self.language_model.predict(text.replace("\n", ""), k=1)
        lang = lang[0].replace("__label__", "")
        prob = prob[0]
        return lang, prob
    
    
    def embed_text(self, text:str|list[str]) -> np.ndarray:
        """
        returns normalized embeddings of shape [N, emb_dim].
        """
        embs =  self.emb_model.encode(text, convert_to_numpy=True).reshape(-1, self.emb_dims)
        embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
        return embs

    
    # def predict_music(self, text):
    #     if isinstance(text, str):
    #         text = [text]
            
    #     classes = ["music", "non-music"]
    #     prediction = self.music_model(text, classes, multi_label=False, hypothesis_template="The topic of this Youtube video is {}.")
    #     pred = [(p["labels"][0], p["scores"][0]) for p in prediction]
    #     return pred
