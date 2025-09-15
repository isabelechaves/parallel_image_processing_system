"""
Módulo de filtros de imagem para processamento paralelo.
Implementa filtro negativo e limiarização com fatiamento.
"""

from typing import Tuple
from pgm_image import PGMImage


def apply_negative_filter(image: PGMImage, row_start: int, row_end: int) -> bytes:
    """
    Aplica filtro negativo em um conjunto de linhas da imagem.
    
    Fórmula: s = T(r) = L - 1 - r = 255 - r
    onde r é o pixel de entrada e L é o valor máximo (255 para PGM P5).
    
    Args:
        image: Imagem PGM de referência
        row_start: Linha inicial (inclusiva)
        row_end: Linha final (exclusiva)
        
    Returns:
        Dados processados das linhas
    """
    processed_data = bytearray()
    
    for y in range(row_start, row_end):
        for x in range(image.w):
            # Obter pixel original
            original_pixel = image.get_pixel(x, y)
            
            # Aplicar filtro negativo: novo_pixel = 255 - pixel_original
            new_pixel = 255 - original_pixel
            
            processed_data.append(new_pixel)
    
    return bytes(processed_data)


def apply_slice_filter(image: PGMImage, row_start: int, row_end: int, 
                      t1: int, t2: int) -> bytes:
    """
    Aplica filtro de limiarização com fatiamento em um conjunto de linhas.
    
    Mantém valores dentro da faixa [t1, t2] e suprime os demais.
    
    Args:
        image: Imagem PGM de referência
        row_start: Linha inicial (inclusiva)
        row_end: Linha final (exclusiva)
        t1: Limite inferior
        t2: Limite superior
        
    Returns:
        Dados processados das linhas
    """
    processed_data = bytearray()
    
    for y in range(row_start, row_end):
        for x in range(image.w):
            # Obter pixel original
            original_pixel = image.get_pixel(x, y)
            
            # Aplicar filtro de limiarização
            if original_pixel <= t1 or original_pixel >= t2:
                new_pixel = 255  # Suprimir (branco)
            else:
                new_pixel = original_pixel  # Manter original
            
            processed_data.append(new_pixel)
    
    return bytes(processed_data)


def process_image_rows(image: PGMImage, row_start: int, row_end: int, 
                      mode: int, t1: int = 0, t2: int = 0) -> bytes:
    """
    Processa um conjunto de linhas da imagem com o filtro especificado.
    
    Args:
        image: Imagem PGM de referência
        row_start: Linha inicial (inclusiva)
        row_end: Linha final (exclusiva)
        mode: Modo de processamento (0=negativo, 1=slice)
        t1: Limite inferior para slice
        t2: Limite superior para slice
        
    Returns:
        Dados processados das linhas
    """
    if mode == 0:
        # Filtro negativo
        return apply_negative_filter(image, row_start, row_end)
    elif mode == 1:
        # Filtro de limiarização
        return apply_slice_filter(image, row_start, row_end, t1, t2)
    else:
        raise ValueError(f"Modo de processamento inválido: {mode}")


def create_processed_image(original_image: PGMImage, processed_data: bytes) -> PGMImage:
    """
    Cria uma nova imagem PGM com os dados processados.
    
    Args:
        original_image: Imagem original de referência
        processed_data: Dados processados
        
    Returns:
        Nova imagem PGM processada
    """
    processed_image = PGMImage(original_image.w, original_image.h, original_image.maxv)
    processed_image.data = processed_data
    return processed_image
