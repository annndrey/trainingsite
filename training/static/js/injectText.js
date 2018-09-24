function injectText(element, type){
    var elem=document.getElementsByName(element)[0];
    var tag2 = "\'>";

    if (type == 'link'){
	var tag1 = "<a href=\'";
	var tag3 = "</a>";
    }
    else if (type == 'pict'){
	var tag1 = "<img width=400 src=\'";
    }

    if(document.selection){
	elem.focus();
	sel=document.selection.createRange();
	if (type == 'link'){
            elem.value=val_start+tag1+text+tag2+text+tag3+val_end;
        }
	else if(type == 'pict'){
            elem.value=val_start+tag1+text+tag2+val_end;
        }
	return;
    }if(elem.selectionStart||elem.selectionStart=="0"){
	var t_start=elem.selectionStart;
	var t_end=elem.selectionEnd;
	var val_start=elem.value.substring(0,t_start);
	var val_end=elem.value.substring(t_end,elem.value.length);
	var text = elem.value.substring(t_start,t_end)
	if (type == 'link'){
	    elem.value=val_start+tag1+text+tag2+text+tag3+val_end;
	}
	else if (type == 'pict'){
	    elem.value=val_start+tag1+text+tag2+val_end;
	}
    }else{
	if (type == 'link'){
            elem.value=val_start+tag1+text+tag2+text+tag3+val_end;
        }
	else if(type == 'pict'){
            elem.value=val_start+tag1+text+tag2+val_end;
        }
    }
}