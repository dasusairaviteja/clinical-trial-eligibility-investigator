"""Deterministic lexical chunk retrieval with original Unicode offsets."""
import re


def retrieve(sources, query, limit=5, chunk_size=1000):
    if not isinstance(query,str) or len(query)>200 or type(limit) is not int or not 1<=limit<=5:
        raise ValueError('invalid retrieval request')
    if type(chunk_size) is not int or not 100<=chunk_size<=4000:
        raise ValueError('invalid chunk size')
    terms = set(re.findall(r'\w+',query.casefold()))
    ranked = []
    for source in sources:
        for start in range(0,len(source.text),chunk_size):
            text = source.text[start:start+chunk_size]
            score = len(terms & set(re.findall(r'\w+',text.casefold())))
            if score or not terms:
                ranked.append((score,source.source_id,source.version,start,text))
    ranked.sort(key=lambda row:(-row[0],row[1],row[2],row[3]))
    return [{'source_id':sid,'source_version':version,'start':start,'end':start+len(text),
             'text':text,'score':score} for score,sid,version,start,text in ranked[:limit]]
