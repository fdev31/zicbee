var song_id=null;
var refresh_interval=5000;

function wget(what) {
    new Request.JSON({url:what, method: "get"}).send();
    //window.location.reload();
    return false;
};

function print_playlist(pls) {
    var txt = "<ul>";
    var s=null;
    for (var i=0; i<pls.length; i++) {
        s = pls[i];
        txt += "<li><a href='"+s[0]+"'>"+s[1] + " - " + s[3] + " ("+s[2]+") </li>";
    }
    txt += "</ul>";
    $('playlist').innerHTML = txt

}

function refresh_infos(infos) {
    if (song_id != infos['id']) {
        song_id = infos['id'];
        if (song_id) {
            txt = "Song "+infos['pls_position']+'/'+infos['pls_size']+"<br/>";
            txt += "<a href='/search/get/song?id="+song_id+"'><b>" + infos['artist'] + "</b> - " + infos['title'] + "</a><br/>";
            txt += infos['album'];
            $('progressbase').tween('width', infos['length']);
            $('progressbar').tween('width', infos['song_position']/2);
            new Request.JSON({url: 'playlist?fmt=json&res=10&start='+(infos['pls_position']+1), method: "get", onSuccess: print_playlist}).send();
        } else {
            txt = "<h2>No song played</h2>";
        }
        $('descr').innerHTML = txt;
    } else {
        $('progressbar').tween('width', infos['song_position']/2);
    }
    tick.delay(refresh_interval);
};
function tick() {
    new Request.JSON({url:'infos?fmt=json', method: "get", onSuccess: refresh_infos}).send();
};
window.addEvent('domready', function() {
        $('progressbar').set('tween', {'duration':refresh_interval});
        tick.delay(refresh_interval);
    });

