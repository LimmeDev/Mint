"""
Core Assistant module for the Mint AI Framework.
"""

import logging
from typing import Dict, List, Optional, Union

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedModel, PreTrainedTokenizer

from mint.config import get_config

logger = logging.getLogger(__name__)


class Assistant:
    """
    Assistant class for generating responses using transformer models.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the assistant with a model and tokenizer.

        Args:
            model_path: Path to the model or model identifier from huggingface.co/models
            device: Device to use for inference (cuda, cpu)
            **kwargs: Additional keyword arguments for model configuration
        """
        config = get_config()
        self.model_path = model_path or config.model_path
        self.device = device or config.device
        
        logger.info(f"Loading model from {self.model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            **kwargs
        )
        self.model.to(self.device)
        logger.info(f"Model loaded on {self.device}")

    def generate(
        self,
        prompt: str,
        max_length: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate a response for the given prompt.

        Args:
            prompt: Input text to generate a response for
            max_length: Maximum length of the generated text
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter
            **kwargs: Additional keyword arguments for generation

        Returns:
            str: Generated text response
        """
        config = get_config()
        max_length = max_length or config.max_length
        temperature = temperature or config.temperature
        top_p = top_p or config.top_p
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Set up generation parameters
        gen_kwargs = {
            "max_length": max_length,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": temperature > 0,
            **kwargs
        }
        
        # Generate response
        with torch.no_grad():
            output_ids = self.model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                **gen_kwargs
            )
        
        # Decode and return the generated text
        generated_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        # Remove the original prompt from the generated text
        response = generated_text[len(prompt):].strip()
        return response
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate a response in a chat context.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional keyword arguments for generation

        Returns:
            str: Generated assistant response
        """
        # Format messages into a prompt
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant: "
        
        # Generate and return response
        response = self.generate(prompt, **kwargs)
        return response 