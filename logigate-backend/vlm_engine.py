import threading
import numpy as np
import torch
from PIL import Image


class VLMEngine:
    def __init__(self):
        self.model = None
        self.processor = None
        self._lock = threading.Lock()

    def load(self):
        print("--- Cargando Qwen2.5-VL-3B-Instruct (VLM local) ---")
        try:
            try:
                from transformers import Qwen2_5_VLForConditionalGeneration as ModelCls
            except ImportError:
                from transformers import Qwen2VLForConditionalGeneration as ModelCls
            from transformers import AutoProcessor

            # GTX 1650 (4GB VRAM): fp16 (~6GB) no cabe → device_map="auto" hacía
            # offload a disco = lentísimo. Cuantización 4-bit (nf4) baja a ~2.5GB,
            # cabe entero en GPU sin offload → mucho más rápido.
            model_kwargs = {}
            if torch.cuda.is_available():
                try:
                    from transformers import BitsAndBytesConfig

                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                    )
                    model_kwargs["device_map"] = {"": 0}  # todo en GPU 0, sin offload
                except ImportError:
                    print("--- bitsandbytes no disponible, cargando sin cuantizar ---")
                    model_kwargs["torch_dtype"] = "auto"
                    model_kwargs["device_map"] = "auto"
            else:
                model_kwargs["torch_dtype"] = "auto"
                model_kwargs["device_map"] = "auto"

            self.model = ModelCls.from_pretrained(
                "Qwen/Qwen2.5-VL-3B-Instruct",
                **model_kwargs,
            )
            self.processor = AutoProcessor.from_pretrained(
                "Qwen/Qwen2.5-VL-3B-Instruct",
                min_pixels=256 * 28 * 28,
                max_pixels=256 * 28 * 28,
            )
            print("--- VLM Qwen2.5-VL-3B listo (4-bit GPU) ---")
        except Exception as e:
            print(f"Error al cargar VLM: {e}")
            self.model = None
            self.processor = None

    @property
    def ready(self):
        return self.model is not None and self.processor is not None

    def interpret(self, img_bgr: np.ndarray, detecciones: list) -> str:
        if not self.ready:
            return ""
        with self._lock:
            try:
                from qwen_vl_utils import process_vision_info

                pil_img = Image.fromarray(img_bgr[:, :, ::-1])

                labels = [d["tipo"] for d in detecciones]
                ctx = f"El sistema detectó: {', '.join(labels)}. " if labels else ""

                prompt = (
                    ctx
                    + "Eres inspector de daños vehiculares. Describe los daños visibles en la imagen: "
                    "zona del vehículo afectada, tipo de daño y severidad estimada. "
                    "Responde en español, máximo 2 oraciones, sin markdown ni listas."
                )

                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "image", "image": pil_img},
                        {"type": "text", "text": prompt},
                    ],
                }]

                text_input = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                image_inputs, video_inputs = process_vision_info(messages)
                inputs = self.processor(
                    text=[text_input],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt",
                )

                device = "cuda" if torch.cuda.is_available() else "cpu"
                inputs = inputs.to(device)

                with torch.no_grad():
                    generated = self.model.generate(
                        **inputs, max_new_tokens=96, do_sample=False
                    )

                trimmed = [out[len(inp):] for inp, out in zip(inputs["input_ids"], generated)]
                return self.processor.batch_decode(
                    trimmed,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )[0].strip()

            except Exception as e:
                print(f"VLM interpret error: {e}")
                return ""
