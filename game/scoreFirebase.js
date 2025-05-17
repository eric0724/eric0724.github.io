
import { database, ref, get, set } from "../js/firebase.js";
function getfirbase(data){
    var nameRef = ref(database, data);
    return get(nameRef).then((snapshot) => {
        if (snapshot.exists()) {
            return snapshot.val();
        } else {
            window.alert(data+"資料不存在");
            return null;
        }
    }).catch((error) => {
        window.alert("讀取失敗：", error);
        return null;
    });
}
window.getfirbase = getfirbase;