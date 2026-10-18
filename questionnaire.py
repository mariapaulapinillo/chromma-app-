QUESTIONNAIRE_SCHEMA = {
    "section_1_colorimetry": [
        {"id": "skin_tone", "q": "1. ¿Cuál describe mejor tu tono de piel natural?", "options": ["Muy clara / Porcelana", "Clara", "Media / Levemente bronceada", "Morena / Olival", "Oscura / Profunda"]},
        {"id": "undertone_self", "q": "2. Sin maquillaje, ¿qué matiz notas principalmente en tu piel?", "options": ["Rosado / Rojizo / Azulado", "Dorado / Amarillento / Durazno", "Verdoso / Cetrino", "Neutro (difícil de notar)"]},
        {"id": "veins", "q": "3. Mira las venas de tu muñeca bajo luz natural. ¿De qué color lucen?", "options": ["Azules o violetas", "Verdes u oliváceas", "Mezcla de azules y verdes", "No se distinguen fácilmente"], "has_visual_aid": True},
        {"id": "sun_reaction", "q": "4. ¿Cómo reacciona tu piel tras exponerse al sol sin bronceador?", "options": ["Se quema muy fácil, casi nunca se broncea", "Se quema primero, luego logra un leve bronceado", "Rara vez se quema, se broncea con facilidad", "Se broncea intensamente sin quemarse"]},
        {"id": "metal_test", "q": "5. ¿Qué accesorios metálicos iluminan mejor tu rostro?", "options": ["Plata, oro blanco o platino", "Oro amarillo, bronce o cobre", "Ambos me lucen igual de bien", "Ninguno resalta en particular"]},
        {"id": "white_test", "q": "6. ¿Qué tono de blanco te favorece más cerca del rostro?", "options": ["Blanco puro / Blanco óptico radiante", "Blanco marfil / Blanco crema / Hueso", "Ambos por igual", "Gris claro o beige preferiblemente"]},
        {"id": "clothing_colors", "q": "7. ¿Con cuál grupo de colores recibes más cumplidos?", "options": ["Pasteles, fríos y suavemente lavados (mora, rosa pastel, azul marino)", "Cálidos, intensos y terrosos (mostaza, terracota, verde oliva)", "Vivos, puros y contrastantes (rojo puro, azul rey, negro)", "Cálidos, luminosos y claros (durazno, coral, verde manzana)"]},
        {"id": "hair_natural_color", "q": "8. ¿Cuál es tu color de cabello natural?", "options": ["Rubio muy claro / Platino / Ceniza", "Rubio dorado / Cobrizo / Castaño claro cálido", "Castaño medio / Castaño oscuro", "Negro azabache / Negro profundo"]},
        {"id": "hair_highlights", "q": "9. Bajo la luz del sol, ¿qué reflejos destacan en tu cabello?", "options": ["Reflejos dorados, rojizos o cobrizos", "Reflejos cenizas, plateados o neutros", "Sin reflejos visibles"]},
        {"id": "eye_color", "q": "10. ¿De qué color son tus ojos?", "options": ["Azul claro, gris o verde claro", "Azul profundo, avellana o café claro", "Café oscuro, marrón profundo o negro", "Verde oliva, miel o ámbar"]},
        {"id": "eye_pattern", "q": "11. Al mirar detenidamente tu iris, ¿qué patrón observas?", "options": ["Destellos dorados o amarillos en el centro", "Anillo gris/azulado alrededor o aspecto limpio/cristalino", "Trama suave, aterciopelada y uniforme"]},
        {"id": "contrast_level", "q": "12. ¿Qué nivel de contraste hay entre tu piel, cabello y ojos?", "options": ["Alto contraste (ej. piel clara y cabello/ojos muy oscuros)", "Medio contraste", "Bajo contraste (todos mis rasgos son de intensidad similar)"]},
        {"id": "blush_natural", "q": "13. Cuando te ruborizas naturalmente (por ejercicio o pena), tu piel luce:", "options": ["Rosada / Fucsia", "Durazno / Coralino", "Rojiza / Cálida", "Casi no me ruborizo"]},
        {"id": "freckles", "q": "14. Si tienes pecas, ¿de qué color son predominantemente?", "options": ["Doradas / Marrones claras / Cobrizas", "Grisáceas / Marrones frías", "No tengo pecas"]},
        {"id": "lip_natural_tone", "q": "15. El color natural de tus labios tiende a ser:", "options": ["Rosa pálido / Violáceo / Morado suave", "Melocotón / Coral / Rosado cálido", "Rojo pálido / Marrón claro", "Oscuro / Pigmentado"]},
        {"id": "bright_vs_muted", "q": "16. ¿Qué tipo de maquillaje de labios te resalta mejor?", "options": ["Tonos vibrantes e intensos (fucsia, rojo puro)", "Tonos suaves, desaturados o nude", "Tonos oscuros y profundos (vino, borgoña)"]},
        {"id": "black_clothing", "q": "17. ¿Cómo te ves usando ropa color negro absoluto cerca de la cara?", "options": ["Me resalta y estiliza la mirada", "Me endurece las facciones o me hace lucir cansada/pálida", "Luces bien solo si uso maquillaje"]},
        {"id": "orange_vs_pink", "q": "18. Entre un labial Naranja Cálido y un Labial Rosa Frío:", "options": ["El Naranja me ilumina; el Rosa me apaga", "El Rosa me favorece; el Naranja me hace lucir amarilla", "Ambos me quedan bien", "Ninguno me favorece particularmente"]},
        {"id": "tan_durability", "q": "19. Tu bronceado dura en el tiempo:", "options": ["Mucho tiempo, el tono se mantiene semanas", "Se desvanece muy rápido", "No me bronceo"]},
        {"id": "eyebrow_density", "q": "20. El tono natural de tus cejas respecto a tu piel es:", "options": ["Muy marcado y definido (oscuro)", "Suave, rubio o castaño claro", "Medio"]},
        {"id": "jewelry_gems", "q": "21. ¿Qué piedras/gemas combinan mejor con tu rostro?", "options": ["Rubí, esmeralda, zafiro (colores joya puros)", "Ámbar, turquesa, ojo de tigre (colores cálidos)", "Perlas, cuarzo rosa, amatista (colores suaves/fríos)"]},
        {"id": "season_known", "q": "22. ¿Te han realizado un análisis de colorimetría previamente?", "options": ["No, nunca", "Sí, me indicaron tonos Cálidos / Primavera / Otoño", "Sí, me indicaron tonos Fríos / Verano / Invierno"]},
        {"id": "makeup_dislike", "q": "23. ¿Qué tono de maquillaje sientes que te luce fatal?", "options": ["Tonos naranjas / dorados", "Tonos rosados / azulados", "Tonos muy oscuros", "Tonos muy pálidos / neon"]},
        {"id": "saturations", "q": "24. En general, te favorecen más los colores:", "options": ["Luminosos y puros (Alta saturación)", "Opacos, grises o empolvados (Baja saturación)", "Oscuros y profundos (Alta densidad)"]}
    ],
    "section_2_skin_type": [
        {"id": "skin_type", "q": "25. ¿Cuál es tu tipo de piel habitual?", "options": ["Grasa (brillo en todo el rostro, poros dilatados)", "Mixta (zona T grasa, mejillas normales/secas)", "Seca (sensación de tirantez, opaca)", "Normal (equilibrada, sin exceso de grasa o sequedad)", "Sensible (tendencia a rojeces/irritación)"]}
    ],
    "section_3_preferences": [
        {"id": "finish_preference", "q": "26. ¿Qué acabado prefieres para la base de maquillaje/piel?", "options": ["Mate (sin brillo, control de grasa)", "Satinado / Natural (aspecto saludable y fresco)", "Luminoso / Dewy (jugoso, radiante, hidratado)"]},
        {"id": "budget_range", "q": "27. ¿Cuál es tu rango de presupuesto estimado por producto?", "options": ["Económico (Hasta $50,000 COP)", "Medio ($50,000 - $100,000 COP)", "Premium ($100,000 - $180,000 COP)", "Sin restricción de presupuesto"]}
    ]
}
