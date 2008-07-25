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
        txt += "<li>"+render_song(s);
    }
    txt += "</ul>";
    $('playlist').innerHTML = txt

}

function validateForm() {
    Cookie.write('host', unescape($('fill_form').host.value));
    Cookie.write('pattern', unescape($('fill_form').pattern.value));
    wget('/search?fmt=txt&host='+$('fill_form').host.value+'&pattern='+$('fill_form').pattern.value);
    hideableForm.toggle();
};

function render_song(infos) {
        if ( $type(infos) == 'array' ) {
            return "<a href='http://"+Cookie.read('host')+infos[0]+"'><font class='listFont'>"+infos[1] + " - " + infos[3] + " ("+infos[2]+")</font></a>";
        } else { // dict like (object)
            return "<a href='http://"+Cookie.read('host')+"/search/get/song.mp3?id="+infos['id']+"'><font class='songfont'>"+infos['artist'] + " - " + infos['title'] + " ("+infos['album']+")</font></a>";
        }
};

function refresh_infos(infos) {
    if (song_id != infos['id']) {
        song_id = infos['id'];
        if (song_id) {
            txt = "Song "+infos['pls_position']+'/'+infos['pls_size']+" : "+render_song(infos);
            $('progressbase').tween('width', infos['length']);
            $('progressbar').tween('width', infos['song_position']/2);
            new Request.JSON({url: 'playlist?fmt=json&res=10&start='+(infos['pls_position']+1), method: "get", onSuccess: print_playlist}).send();
            if (animatedBee.song != song_id) {
                animatedBee.song = song_id;
                animatedBee.start();
            };
        } else {
            animatedBee.stop();
            txt = "<h2>No song played</h2>";
            $('progressbase').tween('width', 0);
        }
        $('descr').innerHTML = txt;
    } else {
        $('progressbar').tween('width', infos['song_position']/2);
    }
};
function tick() {
    new Request.JSON({url:'infos?fmt=json', method: "get", onSuccess: refresh_infos}).send();
};


var animatedBee = {
    song : null,

    in_progress : false,

    setup : function() {
        $('bee').set('tween', {'duration':80});
        return this;
       },
    start : function() {
            this.stop();
            this.in_progress = this.step.periodical(100);
            this.stop.delay(10000);
        },
    step : function() {
           $('bee').tween('margin-left', $random(-30, 0));
       },
    stop : function () {
           if(this.in_progress) {
               $clear(this.in_progress);
               this.in_progress = false;
               $('bee').tween.delay(80, $('bee'), new Array(['margin-left', 0]));
           };
       },
};

var hideableForm = {
    Create : function(e) {
        this.elt = e;
        this.hidden = false;
        return this;
    },
    toggle: function() {
        if (this.hidden) {
            this.elt.tween('left', -1);
            this.hidden = false;
        } else {
            this.elt.tween('left', -400);
            this.hidden = true;
        };
    },
}

/*
function toto() {
    $$('.blockcmd').each(function(el) {
        el.set('tween', {duration: 3000});
        el.addEvent('mouseenter', function() {
            el.tween('background-color', '#c50');
            });
        el.addEvent('mouseout', function() {
            el.tween('background-color', '#000');
            });
        });

    };
*/

window.addEvent('domready', function() {
        animatedBee = animatedBee.setup();
        $('progressbar').set('tween', {'duration':refresh_interval*10});
        tick();
        tick.periodical(refresh_interval);

        document.body.innerHTML += '<img id="flowers" src="/static/pics/flowers.png" />';
        if (! $chk(Cookie.read('host'))) {
            Cookie.write('host', 'localhost', {duration: 30});
            Cookie.write('pattern', '', {duration: 30});
        };
        validateForm.delay(300);
        hideableForm.Create($('fill_form'));
        $('bee').addEvent('click', function() {hideableForm.toggle()});
    });

