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
    var idx=null;
    for (var i=0; i<pls.length; i++) {
        s = pls[i];
        idx = s[6];
        txt += "<li>"+render_song(s)+"<a href='/delete?idx="+idx+"'>[X]</a><a href='/move?i1="+(idx-1)+"&i2="+idx+"'>[^]</a><a href='/move?i1="+idx+"&i2="+(idx+1)+"'>[v]</a>";
    }
    txt += "</ul>";
    $('playlist').innerHTML = txt
        /*
    $$('.listFont').each( function(e) {
            e.addEvent('mouseover', function() {e.tween('color', '#ffb');});
            e.addEvent('mouseout', function() {e.tween('color', '#000');});
            } )
            */

};

function active_icon(name, action) {
    return '<div class="blockcmd"><img onmouseout=\'this.src="/static/pics/cmd/'+name+'.png";\' onmouseover=\'this.src="/static/pics/cmd/'+name+'_sel.png";\' onclick=\''+action+'\' src="/static/pics/cmd/'+name+'.png" /></div>'
};

function fill_cmdgroup() {
    var cmdgroup = $('cmdgroup');
    var g_name;
    var g_action;
    var offset = 0;

    var groups = [
        'search', 'document.location="/db/";',
        'back', 'wget("prev");',
        'next', 'wget("next");',
        'shuffle', 'wget("shuffle");',
        'pause', 'wget("pause");'
    ];

    while ( offset < groups.length ) {
        g_name = groups[offset];
        delete groups[offset];

        g_action = groups[offset+1];
        delete groups[offset+1];

        cmdgroup.innerHTML += active_icon(g_name, g_action);
        offset += 2;
    }
};

function validateForm() {
    Cookie.write('host', unescape($('fill_form').host.value));
    Cookie.write('pattern', unescape($('fill_form').pattern.value));
    wget('/search?fmt=txt&host='+$('fill_form').host.value+'&pattern='+$('fill_form').pattern.value);
    hideableForm.toggle();
};

function render_song(infos) {
        if ( $type(infos) != 'array' ) {
            // Convert to array
            infos = [ infos['uri'],
                  infos['artist'],
                  infos['album'],
                  infos['title']
                  ];
        }
        return "<a href='"+infos[0]+"'><font class='listFont'>"+infos[1] + " - " + infos[3] + " ("+infos[2]+")</font></a>";
};

function refresh_infos(infos) {
    if (song_id != infos['id']) {
        song_id = infos['id'];
        if (song_id) {
            txt = "Song "+infos['pls_position']+'/'+infos['pls_size']+" : "+render_song(infos);
            $('progressbase').tween('width', infos['length']);
            $('progressbar').tween('width', 0);
            new Request.JSON({url: 'playlist?fmt=json&res=10&start='+(infos['pls_position']+1), method: "get", onSuccess: print_playlist}).send();
            if (animatedBee.song != song_id) {
                animatedBee.song = song_id;
                animatedBee.start();
                animatedBee.stop.delay(10000);
            }
        } else {
            animatedBee.stop();
            txt = "<h2>No song played</h2>";
            $('progressbase').tween('width', 0);
        }
        $('descr').innerHTML = txt;
    } else {
        $('progressbar').set('tween', {'duration':refresh_interval+500});
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
       },
    start : function() {
            animatedBee.stop();
            animatedBee.in_progress = animatedBee.step.periodical(80);
        },
    step : function() {
           $('bee').set('tween', {'duration':80});
           $('bee').tween('margin-left', $random(-30, 0));
       },
    stop : function () {
           if(animatedBee.in_progress) {
               $clear(animatedBee.in_progress);
               animatedBee.in_progress = false;
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
};

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
        fill_cmdgroup();
        animatedBee.setup();
        tick();
        tick.periodical(refresh_interval);

        document.body.innerHTML += '<img id="flowers" src="/static/pics/flowers.png" />';
        if (! $chk(Cookie.read('host'))) {
            Cookie.write('host', 'localhost', {duration: 30});
            Cookie.write('pattern', '', {duration: 30});
        };
        hideableForm.Create($('fill_form'));
        hideableForm.toggle(); // auto hide the form
        $('bee').addEvent('click', function() {hideableForm.toggle()});
    });

