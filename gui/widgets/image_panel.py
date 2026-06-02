import customtkinter as ctk
from PIL import Image, ImageTk


class ImagePanel(ctk.CTkFrame):
    # widget d'affichage d'image avec placeholder et chargement dynamique
    def __init__(self, master, width=400, height=400, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.image_width = width
        self.image_height = height
        self._photo = None

        self.configure(fg_color="#1e1e2e")
        self.pack_propagate(False)

        self._placeholder = ctk.CTkLabel(
            self,
            text="Aucune image selectionnee",
            text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self._image_label = ctk.CTkLabel(self, text="")
        self._image_label.place(relx=0.5, rely=0.5, anchor="center")

    def load_image(self, path: str) -> None:
        # charge et redimensionne l'image en conservant le ratio
        img = Image.open(path).convert("RGBA")
        img.thumbnail((self.image_width, self.image_height), Image.LANCZOS)
        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self._photo = ctk_image
        self._image_label.configure(image=ctk_image)
        self._placeholder.place_forget()

    def clear(self) -> None:
        self._image_label.configure(image=None)
        self._photo = None
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")
