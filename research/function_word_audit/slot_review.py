"""Reviewed grammatical slots; exact example spans, not English-label guessing."""
import re
from html import escape
from check import plain

# Language, word, pattern -> label, type, one exact chunk per existing example.
# None means the example does not realise this slot in the displayed order.
REVIEW = {
 ('pt','em',1):('verb','verb',['Viajo','nasceu','Terminaremos','começa','voltam']),
 ('pt','para',1):('verb','verb',['Estudo','Trabalho','Ligou','Paramos','Correu']),
 ('pt','para',2):('noun / noun phrase','noun',['um presente','uma carta','jantar','lugar','um bilhete']),
 ('pt','com',1):('verb','verb',['Escrevo','abriu','Ouvimos','Cortei','Tratou']),
 ('pt','por',0):('verb / expression','mixed',['Obrigado','Espero','foi elogiado','Pagou','Agradeço']),
 ('pt','por',1):('verb','verb',['Caminho','Passamos','Olhou','entrou','Viajamos']),
 ('pt','como',0):('verb','verb',['canta','agiu','brilham','Faz','Correu']),
 ('pt','sobre',0):('verb / noun phrase','mixed',['Falamos','um livro','discutiram','saber','um ensaio']),
 ('pt','sobre',1):('verb','verb',['está','ergue-se','Deixou','ficaram','brilhava']),
 ('pt','até',0):('verb','verb',['Vou caminhar','Ficamos','Espere','Trabalhou','Dirigiram']),
 ('pt','tudo',0):('verb','verb',['está','correu','mudou',None,'ficou']),
 ('es','en',0):('verb','verb',['Vivo','Estamos','Trabaja','quedamos','está guardado']),
 ('es','en',1):('verb','verb',['Viajamos','Nació','Estará','comienzan','Volveremos']),
 ('es','por',0):('verb / expression','mixed',['Gracias','preocupas','Lucharon','Pagó','Fue premiado']),
 ('es','por',1):('verb','verb',['Paseo','Caminamos','Miró','entró','Viajamos']),
 ('es','para',0):('verb','verb',['Estudio','Ahorro','Llamé','detuvimos','Trabajan']),
 ('es','con',1):('verb','verb',['Escribo','Abrió','Escuchó','Cortó','Trató']),
 ('es','como',0):('verb','verb',['Canta','Corre','Brilla','Actuó','Habla']),
 ('es','todo',0):('verb','verb',['está','salió','cambió',None,'quedó']),
}

def apply(lang,word,index,relation):
    row=REVIEW.get((lang,word,index))
    if not row:return []
    label,kind,chunks=row
    relation['formulaHTML']=re.sub(r'(<span class="fw-token-v">).*?(</span>)',lambda m:m[1]+escape(label)+m[2],relation['formulaHTML'])
    relation['slotTypes']['v']=kind
    assert len(chunks)==len(relation['examples'])
    notes=[]
    for j,(example,chunk) in enumerate(zip(relation['examples'],chunks)):
        if chunk is None:
            notes.append(dict(example=j,issue='The focus word is an object before no following verb here; this example needs a separate word-order pattern.'))
            continue
        original=example['targetHTML']
        html=re.sub(r'<span class=[\'"]fw-token-v[\'"]>(.*?)</span>',r'\1',original)
        # Match only outside existing highlight spans. Do not nest or recolour other slots.
        parts=re.split(r'(<span\b[^>]*>.*?</span>)',html)
        matches=[]
        for k in range(0,len(parts),2):
            matches.extend((k,m) for m in re.finditer(r'(?<!\w)'+re.escape(escape(chunk))+r'(?!\w)',parts[k]))
        if len(matches)!=1:raise ValueError((lang,word,index,j,chunk,'ambiguous or missing span'))
        k,m=matches[0];parts[k]=parts[k][:m.start()]+f'<span class="fw-token-v">{m[0]}</span>'+parts[k][m.end():]
        example['targetHTML']=''.join(parts)
        assert plain(original)==plain(example['targetHTML'])
    relation['targetHTML']=relation['examples'][0]['targetHTML']
    if notes:relation['previewSlotNotes']=notes
    return notes
