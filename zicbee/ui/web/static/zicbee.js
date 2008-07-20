var song_id=null;
function wget(what) {
    new Request.JSON({url:what, method: "get"}).send();
    //window.location.reload();
    return false;
};
function refresh_infos(infos) {
    if (song_id != infos['__id__']) {
        song_id = infos['__id__'];
        if (song_id) {
            txt = "Song "+infos['pls_position']+'/'+infos['pls_size']+"<br/>";
            txt += "<b>" + infos['artist'] + "</b> - " + infos['title'] + "<br/>";
            txt += infos['album'];
            $('progressbase').tween('width', infos['length']);
        } else {
            txt = "<h2>No song played</h2>";
        }
        $('descr').innerHTML = txt;
    } else {
        $('progressbar').tween('width', infos['song_position']);
    }
    tick.delay(2000);
};
function tick() {
    new Request.JSON({url:'infos?fmt=json', method: "get", onSuccess: refresh_infos}).send();
};
window.addEvent('domready', function() {
        $('progressbar').set('tween', {'duration':2500});
        tick.delay(2000);
    });

