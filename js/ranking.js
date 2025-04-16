
const currentURL = window.location.href;
const currentURLname = currentURL.split("/").pop();
var p_textUI = document.getElementById("ranking")
import { database, ref, get, set } from "../js/firebase.js";
let nameRef = ref(database, "name");
const playerName = localStorage.getItem("playerName");

let namelist = [],GameNamelist = [],scorelist = []; // 全域變數
let rankinglist = []; // 全域變數/*
/*
namelist = [];*/
// 讀取資料
function addfirebase(s){
    /*
    namelist.push(playerName);
    namelist.push(currentURLname);
    namelist.push("score:"+s);
    */
   //window.alert(playerName)
   if(playerName == "undefined" || currentURLname == "undefined" || s == "undefined") window.alert("null")
    else{
        var s_now
        var isNoSamName = true;
        if(namelist.includes(playerName)){
            for(var i=1;i<namelist.length;i++){
                if(namelist[i]==playerName){
                    if(GameNamelist[i]==currentURLname){
                        s_now =  parseInt(scorelist[i].split(":").pop());
                        if(s_now >= s) isNoSamName = false;
                        
                    }
                }
            }
        }
        //window.alert("daf") +parseInt(scorelist[i].split(":").pop())+"\n"
        /*
        for(var i=1;i<namelist.length;i++){
            s_now = parseInt(scorelist[i].split(":").pop());
            window.alert(currentURLname+"\n"+playerName+"\n"+s_now+"\n"+s)
        }*/
        if(isNoSamName){
            namelist.push(playerName);scorelist
            GameNamelist.push(currentURLname);
            scorelist.push("score:"+s);

            nameRef = ref(database, "name");
            set(nameRef, namelist);
            nameRef = ref(database, "GameName");
            set(nameRef, GameNamelist);
            nameRef = ref(database, "score");
            set(nameRef, scorelist);
        }
        showranking()
    }
}
window.addfirebase = addfirebase; // ⬅ 這樣會變成全域函式
showranking()
function showranking(){
    nameRef = ref(database, "name");
    get(nameRef).then((snapshot) => {
        if (snapshot.exists()) namelist = snapshot.val();//list
        nameRef = ref(database, "GameName");
        get(nameRef).then((snapshot) => {
            if (snapshot.exists()) GameNamelist = snapshot.val();//list
            //window.alert(GameNamelist)
            nameRef = ref(database, "score");
            get(nameRef).then((snapshot) => {
                if (snapshot.exists()) scorelist = snapshot.val();//list
                rankinglist = [];
                let x = 1;
                for(var i=1;i<GameNamelist.length;i++){
                    if(GameNamelist[i] == currentURLname){
                        rankinglist.push(namelist[i]);
                        rankinglist.push(scorelist[i]);
                    }
                }
                //window.alert(rankinglist);
                var maxidlist = [],textUItext = "";
                for(var i=1;i < (rankinglist.length );i+=2){
                    var maxid = null; 
                    var max = 0
                    for(var j=1;j < rankinglist.length;j+=2){
                        if(!maxidlist.includes(j)){
                            //window.alert(j+"\n"+maxidlist+"\n"+!maxidlist.includes(j))
                            var s1 =  parseInt(rankinglist[j].split(":").pop())
                            //window.alert(s1);
                            if(s1 > max || maxid == null){
                                //window.alert(j+"\n"+maxidlist)
                                maxid = j ;
                                max =  parseInt(rankinglist[maxid].split(":").pop())
                                //window.alert(max)
                            }
                        }
                    }
                    maxidlist.push(maxid);
                    //window.alert(maxidlist);
                    textUItext += rankinglist[maxid-1] + " " + rankinglist[maxid] + "<br>";
                }
            p_textUI.innerHTML = textUItext;
            p_textUI.style.backgroundColor = "#abababab";
            
            }).catch((error) => {window.alert("錯誤：", error);});
        }).catch((error) => {window.alert("錯誤：", error);});
    }).catch((error) => {window.alert("錯誤：", error);});
}

    

/*
    cardgame.html
    cardgame.html
*/