# Monika's ???? Event
# deserves it's own file because of how much dialogue these have
# it basically shows a new screen over everything, and has an image map
# Monika reacts to he place the player clicks


### initialize the island images
init 1 python:
    ## NOTE: we assume 2 things:
    #   - we have write access to teh mod_assets folder
    #   - the existing pngs dont exist yet
    #
    #   if for some reason we fail to convert the files into images
    #   then we must backout of showing the event.
    #
    #   NOTE: other things to note:
    #       on o31, we cannot have islands event
    mas_cannot_decode_islands = not store.mas_island_event.decodeImages()


init -25 python in mas_island_event:
    import random
    import itertools
    import functools
    from zipfile import ZipFile

    import store
    import store.mas_dockstat as mds
    import store.mas_ics as mis
    from store import (
        mas_utils,
        mas_weather,
        Transform,
        LiveComposite,
        MASWeatherMap,
        MASFilterWeatherDisplayableCustom,
        MASFilterWeatherDisplayable
    )
    from store.mas_parallax import (
        ParallaxSprite,
        ParallaxDecal
    )

    # These are dics, they're being populated later
    # Once we decode the imgs
    island_disp_map = None
    decal_disp_map = None
    bg_disp_map = None
    overlay_disp_map = None

    # setup the docking station we are going to use here
    islands_station = store.MASDockingStation(mis.ISLANDS_FOLDER)

    store.m = None
    # This map holds partials which expect the last agrument - the displayable obj - to be passed in
    # to create sprites/decals/etc
    # NOTE: As you can see ParallaxDecal aren't being passed in partials, they are dynamically added later
    # during composite image building
    # NOTE: Use functools.partial instead of renpy.partial because the latter has an argument conflict. Smh Tom
    PARTIAL_OBJECTS_MAP = {
        "isld": {
            "isld_0": functools.partial(ParallaxSprite, x=374, y=670, z=10, zoom=1.0),
            "isld_1": functools.partial(
                ParallaxSprite,
                x=808,
                y=519,
                z=40,
                zoom=1.0,
                function=None,
                on_click=functools.partial(renpy.invoke_in_new_context, renpy.say, store.m, "Clicked!")
            ),
            "isld_2": functools.partial(
                ParallaxSprite,
                x=462,
                y=393,
                z=90,
                zoom=1.0,
                function=None
            ),
            "isld_3": functools.partial(
                ParallaxSprite,
                x=338,
                y=179,
                z=130,
                zoom=1.0,
                function=None
            ),
            "isld_4": functools.partial(ParallaxSprite, x=182, y=202, z=150, zoom=1.0),
            "isld_5": functools.partial(
                ParallaxSprite,
                x=1135,
                y=270,
                z=50,
                zoom=1.0,
                function=None
            ),
            "isld_6": functools.partial(
                ParallaxSprite,
                x=1013,
                y=112,
                z=200,
                zoom=1.0,
                function=None
            ),
            "isld_7": functools.partial(
                ParallaxSprite,
                x=475,
                y=97,
                z=250,
                zoom=1.0,
                function=None
            ),
            "isld_8": functools.partial(ParallaxSprite, x=563, y=84, z=220, zoom=1.0),
        },
        "decal": {
            "bookshelf": functools.partial(ParallaxDecal, x=91, y=-60, z=4),
            "bushes": functools.partial(ParallaxDecal, x=97, y=-52, z=5),
            "house": functools.partial(ParallaxDecal, x=-14, y=-113, z=1),
            "tree": functools.partial(ParallaxDecal, x=12, y=-210, z=3),
            "glitch": functools.partial(ParallaxDecal, x=-14, y=-113, z=2)
        },
        "bg": {
            "def": functools.partial(
                ParallaxSprite,
                x=renpy.config.screen_width/2.0,
                y=renpy.config.screen_height/2.0,
                z=10000,
                zoom=1.1,
                min_zoom=1.1,
                max_zoom=4.1
            )
        }
    }

    def _select_img(st, at, mfwm):
        """
        Selection function to use in Island-based images

        IN:
            st - renpy related
            at - renpy related
            mfwm - MASFilterWeatherMap for this island

        RETURNS:
            displayable data
        """
        # During winter we always return images with snow
        # Nonideal, but we have to do this because of the tree
        # FIXME: ideal solution would be split the images by seasons too
        if store.mas_isWinter():
            return mfwm.fw_get(store.mas_sprites.get_filter(), store.mas_weather_snow)

        return store.mas_fwm_select(st, at, mfwm)

    def IslandFilterWeatherDisplayable(**filter_pairs):
        """
        DynamicDisplayable for Island images.

        IN:
            **filter_pairs - filter pairs to MASFilterWeatherMap.

        OUT:
            DynamicDisplayable for Island images that respect filters and
                weather.
        """
        return MASFilterWeatherDisplayableCustom(
            _select_img,
            True,
            **filter_pairs
        )

    def shouldDecodeImages():
        """
        A united check whether or not we should decode images in this sesh
        """
        # TODO: add more checks here as needed
        return (
            not store.mas_isO31()
            # and (X or not Y)
        )

    def decodeImages():
        """
        Attempts to decode the iamges

        OUT:
            True upon success, False otherwise
        """
        if not shouldDecodeImages():
            return False

        isld_map = {
            "isld_0": {
                "d": "islds/0/d.obj",
                "d_r": "islds/0/d_r.obj",
                "d_s": "islds/0/d_s.obj",
                "n": "islds/0/n.obj",
                "n_r": "islds/0/n_r.obj",
                "n_s": "islds/0/n_s.obj"
            },
            "isld_1": {
                "d": "islds/1/d.obj",
                "d_r": "islds/1/d_r.obj",
                "d_s": "islds/1/d_s.obj",
                "n": "islds/1/n.obj",
                "n_r": "islds/1/n_r.obj",
                "n_s": "islds/1/n_s.obj"
            },
            "isld_2": {
                "d": "islds/2/d.obj",
                "d_r": "islds/2/d_r.obj",
                "d_s": "islds/2/d_s.obj",
                "n": "islds/2/n.obj",
                "n_r": "islds/2/n_r.obj",
                "n_s": "islds/2/n_s.obj"
            },
            "isld_3": {
                "d": "islds/3/d.obj",
                "d_r": "islds/3/d_r.obj",
                "d_s": "islds/3/d_s.obj",
                "n": "islds/3/n.obj",
                "n_r": "islds/3/n_r.obj",
                "n_s": "islds/3/n_s.obj"
            },
            "isld_4": {
                "d": "islds/4/d.obj",
                "d_r": "islds/4/d_r.obj",
                "d_s": "islds/4/d_s.obj",
                "n": "islds/4/n.obj",
                "n_r": "islds/4/n_r.obj",
                "n_s": "islds/4/n_s.obj"
            },
            "isld_5": {
                "d": "islds/5/d.obj",
                "d_r": "islds/5/d_r.obj",
                "d_s": "islds/5/d_s.obj",
                "n": "islds/5/n.obj",
                "n_r": "islds/5/n_r.obj",
                "n_s": "islds/5/n_s.obj"
            },
            "isld_6": {
                "d": "islds/6/d.obj",
                "d_r": "islds/6/d_r.obj",
                "d_s": "islds/6/d_s.obj",
                "n": "islds/6/n.obj",
                "n_r": "islds/6/n_r.obj",
                "n_s": "islds/6/n_s.obj"
            },
            "isld_7": {
                "d": "islds/7/d.obj",
                "d_r": "islds/7/d_r.obj",
                "d_s": "islds/7/d_s.obj",
                "n": "islds/7/n.obj",
                "n_r": "islds/7/n_r.obj",
                "n_s": "islds/7/n_s.obj"
            },
            "isld_8": {
                "d": "islds/8/d.obj",
                "d_r": "islds/8/d_r.obj",
                "d_s": "islds/8/d_s.obj",
                "n": "islds/8/n.obj",
                "n_r": "islds/8/n_r.obj",
                "n_s": "islds/8/n_s.obj"
            }
        }
        decal_map = {
            "bookshelf": {
                "d": "decals/bookshelf/d.obj",
                "d_r": "decals/bookshelf/d_r.obj",
                "d_s": "decals/bookshelf/d_s.obj",
                "n": "decals/bookshelf/n.obj",
                "n_r": "decals/bookshelf/n_r.obj",
                "n_s": "decals/bookshelf/n_s.obj"
            },
            "bushes": {
                "d": "decals/bushes/d.obj",
                "d_r": "decals/bushes/d_r.obj",
                "d_s": "decals/bushes/d_s.obj",
                "n": "decals/bushes/n.obj",
                "n_r": "decals/bushes/n_r.obj",
                "n_s": "decals/bushes/n_s.obj"
            },
            "house": {
                "d": "decals/house/d.obj",
                "d_r": "decals/house/d_r.obj",
                "d_s": "decals/house/d_s.obj",
                "n": "decals/house/n.obj",
                "n_r": "decals/house/n_r.obj",
                "n_s": "decals/house/n_s.obj"
            },
            "tree": {
                "d": "decals/tree/d.obj",
                "d_r": "decals/tree/d_r.obj",
                "d_s": "decals/tree/d_s.obj",
                "n": "decals/tree/n.obj",
                "n_r": "decals/tree/n_r.obj",
                "n_s": "decals/tree/n_s.obj"
            }
        }
        bg_map = {
            "def": {
                "d": "bg/def/d.obj",
                "d_r": "bg/def/d_r.obj",
                "d_s": "bg/def/d_s.obj",
                "n": "bg/def/n.obj",
                "n_r": "bg/def/n_r.obj",
                "n_s": "bg/def/n_s.obj"
            }
        }
        overlay_map = {
            "rain": {
                "d": "overlays/rain/d.obj",
                "n": "overlays/rain/n.obj"
            },
            "snow": {
                "d": "overlays/snow/d.obj",
                "n": "overlays/snow/n.obj"
            }
        }
        glitch_fns = (
            "glitch/g_0.obj",
            "glitch/g_1.obj",
            "glitch/g_2.obj",
            "glitch/g_3.obj",
            "glitch/g_4.obj",
            "glitch/g_5.obj",
            "glitch/g_6.obj"
        )

        err_msg = "[ERROR] Failed to decode images: {}."

        pkg = islands_station.getPackage("project_or")

        if not pkg:
            mas_utils.writelog(err_msg.format("Missing package"))
            return False

        pkg_data = islands_station.unpackPackage(pkg, pkg_slip=mis.ISLAND_PKG_CHKSUM)

        if not pkg_data:
            mas_utils.writelog(err_msg.format("Bad package."))
            return False

        glitch_frames = None

        def _read_zip(zip_file, map_):
            """
            Inner helper function to read zip and override maps

            IN:
                zip_file - the zip file opened for reading
                map_ - the map to get filenames from, and which will be overriden
            """
            for name, path_map in map_.iteritems():
                for sprite_type, path in path_map.iteritems():
                    raw_data = zip_file.read(path)
                    img = store.MASImageData(raw_data, name + ".png")
                    path_map[sprite_type] = img

        try:
            with ZipFile(pkg_data, "r") as zip_file:
                # Now override maps to contain imgs instead of img paths
                for map_ in (isld_map, decal_map, bg_map, overlay_map):
                    _read_zip(zip_file, map_)

                # Anim frames are handled a bit differently
                glitch_frames = tuple(
                    (store.MASImageData(zip_file.read(fn), fn + ".png") for fn in glitch_fns)
                )

        except Exception as e:
            mas_utils.writelog(err_msg.format(e))
            return False

        else:
            # We loaded the images, now create dynamic displayables
            _buildDisplayables(isld_map, decal_map, bg_map, overlay_map, glitch_frames)

        return True

    def _buildDisplayables(isld_map, decal_map, bg_map, overlay_map, glitch_frames):
        """
        Takes multiple maps with images and builds displayables from them, sets global vars
        NOTE: should be used inside decode_images
        NOTE: no sanity checks, can raise exceptions

        IN:
            isld_map - the map from island names to raw images
            decal_map - the map from decal names to raw images
            bg_map - the map from bg ids to raw images
            overlay_map - the map from overlay ids to raw images
            glitch_frames - tuple of glitch anim frames
        """
        global island_disp_map, decal_disp_map, bg_disp_map, overlay_disp_map

        # Build the islands
        island_disp_map = dict()
        for isld_name, img_map in isld_map.iteritems():
            disp = IslandFilterWeatherDisplayable(
                day=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["d"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["d_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["d_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["d_r"]
                    }
                ),
                night=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["n"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["n_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["n_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["n_r"]
                    }
                )
            )
            island_disp_map[isld_name] = PARTIAL_OBJECTS_MAP["isld"][isld_name](disp)

        # Build the decals
        decal_disp_map = dict()
        for decal_name, img_map in decal_map.iteritems():
            disp = IslandFilterWeatherDisplayable(
                day=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["d"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["d_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["d_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["d_r"]
                    }
                ),
                night=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["n"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["n_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["n_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["n_r"]
                    }
                )
            )
            decal_disp_map[decal_name] = PARTIAL_OBJECTS_MAP["decal"][decal_name](disp)

        # Build the bg
        bg_disp_map = dict()
        for bg_name, img_map in bg_map.iteritems():
            disp = IslandFilterWeatherDisplayable(
                day=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["d"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["d_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["d_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["d_r"]
                    }
                ),
                night=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["n"],
                        mas_weather.PRECIP_TYPE_RAIN: img_map["n_r"],
                        mas_weather.PRECIP_TYPE_SNOW: img_map["n_s"],
                        mas_weather.PRECIP_TYPE_OVERCAST: img_map["n_r"]
                    }
                )
            )
            bg_disp_map[bg_name] = PARTIAL_OBJECTS_MAP["bg"][bg_name](disp)

        # Build the overlays
        overlay_disp_map = dict()
        for overlay_name, img_map in overlay_map.iteritems():
            # Overlays are just dynamic displayables
            overlay_disp_map[overlay_name] = MASFilterWeatherDisplayable(
                True,
                day=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["d"]
                    }
                ),
                night=MASWeatherMap(
                    {
                        mas_weather.PRECIP_TYPE_DEF: img_map["n"]
                    }
                )
            )

        # Build glitch disp
        def _select_glitch_frame(transform, st, at):
            """
            A function which we use as a transform, updates the child
            """
            redraw = random.uniform(0.3, 1.3)
            next_child = random.choice(glitch_frames)

            transform.child = next_child

            return redraw

        glitch_disp = Transform(child=glitch_frames[0], function=_select_glitch_frame)
        decal_disp_map["glitch"] = PARTIAL_OBJECTS_MAP["decal"]["glitch"](glitch_disp)

    def getIslandsImg():
        """
        Builds an image for islands and returns it
        NOTE: This is temporary until we split islands into foreground/background
        NOTE: change the island image definitions when this happens.

        OUT:
            LiveComposite
        """
        # Just in case we always remove all decals and readd them as needed
        for isld in island_disp_map.itervalues():
            isld._container.remove_all()

        island_disp_map["isld_1"]._container.add(
            decal_disp_map["bookshelf"],
            decal_disp_map["bushes"],
            decal_disp_map["house"],
            decal_disp_map["tree"],
            decal_disp_map["glitch"]
        )

        # First add parallax sprites (islands and bg)
        imgs = island_disp_map.values()
        imgs.append(bg_disp_map["def"])
        # In order from back to front
        imgs.sort(key=lambda sprite: sprite.z, reverse=True)

        # Now add overlays (they are always last)
        if store.mas_is_raining:
            imgs.append(overlay_disp_map["rain"])

        elif store.mas_is_snowing:
            imgs.append(overlay_disp_map["snow"])

        def_coords = itertools.repeat((0, 0), len(imgs))
        lc_args = itertools.chain.from_iterable(itertools.izip(def_coords, imgs))

        return LiveComposite(
            (renpy.config.screen_width, renpy.config.screen_height),
            *lc_args
        )

    def isWinterWeather():
        """
        Checks if the weather on the islands is wintery

        OUT:
            boolean:
                - True if we're using snow islands
                - False otherwise
        """
        return store.mas_is_snowing or store.mas_isWinter()

    def isCloudyWeather():
        """
        Checks if the weather on the islands is cloudy

        OUT:
            boolean:
                - True if we're using overcast/rain islands
                - False otherwise
        """
        return store.mas_is_raining or store.mas_current_weather == store.mas_weather_overcast


init 5 python:
    if not mas_cannot_decode_islands:
        addEvent(
            Event(
                persistent.event_database,
                eventlabel="mas_monika_islands",
                category=['monika','misc'],
                prompt="Can you show me the floating islands?",
                pool=True,
                unlocked=False,
                rules={"no_unlock": None, "bookmark_rule": store.mas_bookmarks_derand.WHITELIST},
                aff_range=(mas_aff.ENAMORED, None)
            )
        )

init -876 python in mas_delact:
    # this event requires a delayed aciton, since we cannot ensure that
    # the sprites for this were decoded correctly

    def _mas_monika_islands_unlock():
        return store.MASDelayedAction.makeWithLabel(
            2,
            "mas_monika_islands",
            (
                "not store.mas_cannot_decode_islands"
                " and mas_isMoniEnamored(higher=True)"
            ),
            store.EV_ACT_UNLOCK,
            store.MAS_FC_START
        )


label mas_monika_islands:
    m 1eub "I'll let you admire the scenery for now."
    m 1hub "Hope you like it!"

    # prevent interactions
    $ mas_RaiseShield_core()
    $ mas_OVLHide()
    $ disable_esc()
    $ renpy.store.mas_hotkeys.no_window_hiding = True

    # keep looping the screen
    $ _mas_island_keep_going = True

    # keep track about the window
    $ _mas_island_window_open = True

    # text used for the window
    $ _mas_toggle_frame_text = "Close Window"

    # shimeji flag
    $ _mas_island_shimeji = False

    # random chance to get mini moni appear
    if renpy.random.randint(1,100) == 1:
        $ _mas_island_shimeji = True

    # double screen trick
    show screen mas_islands_background

    # keep showing the event until the player wants to go
    while _mas_island_keep_going:

        # image map with the event
        call screen mas_show_islands()

        if _return:
            # call label if we have one
            call expression _return
        else:
            # player wants to quit the event
            $ _mas_island_keep_going = False
    # hide extra screen
    hide screen mas_islands_background

    # drop shields
    $ mas_DropShield_core()
    $ mas_OVLShow()
    $ enable_esc()
    $ store.mas_hotkeys.no_window_hiding = False

    m 1eua "I hope you liked it, [mas_get_player_nickname()]~"
    return

label mas_island_upsidedownisland:
    m "Oh, that."
    m "I guess you're wondering why that island is upside down, right?"
    m "Well...I was about to fix it until I took another good look at it."
    m "It looks surreal, doesn't it?"
    m "I just feel like there's something special about it."
    m "It's just...mesmerizing."
    return

label mas_island_glitchedmess:
    m "Oh, that."
    m "It's something I'm currently working on."
    m "It's still a huge mess, though. I'm still trying to figure it all out."
    m "In due time, I'm sure I'll get better at coding!"
    m "Practice makes perfect after all, right?"
    return

label mas_island_cherry_blossom_tree:
    python:

        if not renpy.store.seen_event("mas_island_cherry_blossom1"):

            renpy.call("mas_island_cherry_blossom1")

        else:
            _mas_cherry_blossom_events = [
                "mas_island_cherry_blossom1",
                "mas_island_cherry_blossom3",
                "mas_island_cherry_blossom4"
            ]

            if not mas_island_event.isWinterWeather():
                _mas_cherry_blossom_events.append("mas_island_cherry_blossom2")

            renpy.call(renpy.random.choice(_mas_cherry_blossom_events))

    return

label mas_island_cherry_blossom1:
    if mas_island_event.isWinterWeather():
        m "This tree may look dead right now...but when it blooms, it's gorgeous."
    else:
        m "It's a beautiful tree, isn't it?"
    m "It's called a Cherry Blossom tree; they're native to Japan."
    m "Traditionally, when the flowers are in bloom, people would go flower viewing and have a picnic underneath the trees."
    m "Well, I didn't choose this tree because of tradition."
    m "I chose it because it's lovely and pleasing to look at."
    m "Just staring at the falling petals is awe-inspiring."
    if mas_island_event.isWinterWeather():
        m "When it's blooming, that is."
        m "I can't wait until we get the chance to experience that, [player]."
    return

label mas_island_cherry_blossom2:
    m "Did you know you can eat the flower petals of a Cherry Blossom tree?"
    m "I don't know the taste myself, but I'm sure it can't be as sweet as you."
    m "Ehehe~"
    return

label mas_island_cherry_blossom3:
    m "You know, the tree is symbolic like life itself."
    m "Beautiful, but short-lived."
    m "But with you here, it's always blooming beautifully."
    if mas_island_event.isWinterWeather():
        m "Even if it's bare now, it'll blossom again soon."
    m "Know that I'll always be grateful to you for being in my life."
    m "I love you, [player]~"
    # manually handle the "love" return key
    $ mas_ILY()
    return

label mas_island_cherry_blossom4:
    m "You know what'd be nice to drink under the Cherry Blossom tree?"
    m "A little sake~"
    m "Ahaha! I'm just kidding."
    m "I'd rather have tea or coffee."
    if mas_island_event.isWinterWeather():
        m "Or hot chocolate, even. It'd certainly help with the cold."
        m "Of course, even if that failed, we could always cuddle together...{w=0.5} That'd be really romantic~"
    else:
        m "But, it'd be nice to watch the falling petals with you."
        m "That'd be really romantic~"
    return

label mas_island_sky:
    python:

        if mas_current_background.isFltDay():
            _mas_sky_events = [
                "mas_island_day1",
                "mas_island_day2",
                "mas_island_day3"
            ]

        else:
            _mas_sky_events = [
                "mas_island_night1",
                "mas_island_night2",
                "mas_island_night3"
            ]

        _mas_sky_events.append("mas_island_daynight1")
        _mas_sky_events.append("mas_island_daynight2")

        renpy.call(renpy.random.choice(_mas_sky_events))

    return

label mas_island_day1:
    #NOTE: this ordering is key, during winter we only use snow covered islands with clear sky
    # so Winter path needs to be first
    if mas_island_event.isWinterWeather():
        m "What a beautiful day today."
        m "Perfect for taking a walk to admire the scenery."
        m "...Huddled together, so as to stave off the cold."
        m "...With some nice hot drinks to help keep us warm."
    elif mas_is_raining:
        m "Aww, I would've liked to do some reading outdoors."
        m "But I'd rather avoid getting my books wet..."
        m "Soggy pages are a pain to deal with."
        m "Another time, maybe."
    elif mas_current_weather == mas_weather_overcast:
        m "Reading outside with this weather wouldn't be too bad, but it could rain at any moment."
        m "I'd rather not risk it."
        m "Don't worry, [player]. We'll do it some other time."
    else:
        m "It's a nice day today."
        m "This weather would be good for a little book reading under the Cherry Blossom tree right, [player]?"
        m "Lying under the shade while reading my favorite book."
        m "...Along with a snack and your favorite drink on the side."
        m "Ahh, that'd be really nice to do~"
    return

label mas_island_day2:
    #NOTE: this ordering is key, during winter we only use snow covered islands with clear sky
    # so Winter path needs to be first
    if mas_island_event.isWinterWeather():
        m "Have you ever made a snow angel, [player]?"
        m "I've tried in the past, but never had much success..."
        m "It's a lot harder than it looks like."
        m "I bet we'd have a lot of fun, even if whatever we make doesn't end up looking like an angel."
        m "It's just a matter of being a bit silly, you know?"
    elif mas_island_event.isCloudyWeather():
        m "Going outdoors with this kind of weather doesn't look very appealing..."
        m "Maybe if I had an umbrella I'd feel more comfortable."
        m "Imagine both of us, shielded from the rain, inches apart."
        m "Staring into each other's eyes."
        m "Then we start leaning closer and closer until we're almost-"
        m "I think you can finish that thought yourself, [player]~"
    else:
        m "The weather looks nice."
        m "This would definitely be the best time to have a picnic."
        m "We even have a great view to accompany it with!"
        m "Wouldn't it be nice?"
        m "Eating under the Cherry Blossom tree."
        m "Adoring the scenery around us."
        m "Enjoying ourselves with each other's company."
        m "Ahh, that'd be fantastic~"
    return

label mas_island_day3:
    if mas_is_raining and not mas_isWinter():
        m "It's raining pretty heavily..."
        m "I wouldn't want to be outside now."
        m "Though being indoors at a time like this feels pretty cozy, don't you think?"
    else:
        m "It's pretty peaceful outside."
        if mas_island_event.isWinterWeather():
            m "We could have a snowball fight, you know."
            m "Ahaha, that'd be so much fun!"
            m "I bet I could land a shot on you a few islands away."
            m "Some healthy competition never hurt anyone, right?"
        else:
            m "I wouldn't mind lazing around in the grass right now..."
            m "With your head resting on my lap..."
            m "Ehehe~"
    return

label mas_island_night1:
    m "While it's nice to be productive during the day, there's something so peaceful about the night."
    m "The sounds of crickets chirping mixed with a gentle breeze is so relaxing."
    m "You'd hold me on a night like that, right~"
    return

label mas_island_night2:
    if not mas_isWinter() and mas_island_event.isCloudyWeather():
        m "Too bad we can't see the stars tonight..."
        m "I would've loved to gaze at the cosmos with you."
        m "That's alright though, we'll get to see it some other time, then."
    else:
        if seen_event('monika_stargazing'):
            m "Aren't the stars so beautiful, [player]?"
            m "Although, this isn't {i}quite{/i} what I had in mind when I mentioned stargazing before..."
            m "As nice as they are to look at, the part that I want to experience most is being with you, holding each other tight while we lay there."
            m "Someday, [player].{w=0.3} Someday."

        else:
            m "Have you ever gone stargazing, [mas_get_player_nickname()]?"
            m "Taking some time out of your evening to look at the night sky and to just stare at the beauty of the sky above..."
            m "It's surprisingly relaxing, you know?"
            m "I've found that it can really relieve stress and clear your head..."
            m "And seeing all kinds of constellations in the sky just fills your mind with wonder."
            m "Of course, it really makes you realize just how small we are in the universe."
            m "Ahaha..."
    return

label mas_island_night3:
    if not mas_isWinter() and mas_island_event.isCloudyWeather():
        m "Cloudy weather is kind of depressing, don't you think?"
        m "Especially at nighttime, when it hides the stars away from our view."
        m "It's such a shame, really..."
    else:
        m "What a beautiful night!"
        if mas_island_event.isWinterWeather():
            m "There's just something about a cold, crisp night that I love."
            m "The contrast of the dark sky and the land covered in snow is really breathtaking, don't you think?"
        else:
            m "If I could, I'd add fireflies."
            m "Their lights complement the night sky, it's a pretty sight."
            m "Improve the ambience a little, you know?"
    return

label mas_island_daynight1:
    m "Maybe I should add more shrubs and trees."
    m "Make the islands prettier you know?"
    m "I just have to find the right flowers and foliage to go with it."
    m "Or maybe each island should have its own set of plants so that everything will be different and have variety."
    m "I'm getting excited thinking about it~"
    return

label mas_island_daynight2:
    # aurora borealis
    m "{i}~Windmill, windmill for the land~{/i}"

    # a-aurora borealis
    m "{i}~Turn forever hand in hand~{/i}"

    # aurora borealis
    m "{i}~Take it all in on your stride~{/i}"

    # at this time of day?
    m "{i}~It is ticking, falling down~{/i}"

    # aurora borealis
    m "{i}~Love forever, love is free~{/i}"

    # a-aurora borealis
    m "{i}~Let's turn forever, you and me~{/i}"

    # in this part of the country? Yes
    m "{i}~Windmill, windmill for the land~{/i}"

    m "Ehehe, don't mind me, I just wanted to sing out of the blue~"
    return

label mas_island_shimeji:
    m "Ah!"
    m "How'd she get there?"
    m "Give me a second, [player]..."
    $ _mas_island_shimeji = False
    m "All done!"
    m "Don't worry, I just moved her to a different place."
    return

label mas_island_bookshelf:
    python:

        _mas_bookshelf_events = [
            "mas_island_bookshelf1",
            "mas_island_bookshelf2"
        ]

        renpy.call(renpy.random.choice(_mas_bookshelf_events))

    return

label mas_island_bookshelf1:
    #NOTE: this ordering is key, during winter we only use snow covered islands with clear sky
    # so Winter path needs to be first
    if mas_island_event.isWinterWeather():
        m "That bookshelf might not look terribly sturdy, but I'm sure it can weather a little snow."
        m "It's the books that worry me a bit."
        m "I just hope they don't get too damaged..."
    elif mas_island_event.isCloudyWeather():
        m "At times like this, I wish I would've kept my books indoors..."
        m "Looks like we'll just have to wait for better weather to read them."
        m "In the meantime..."
        m "How about cuddling a bit, [player]?"
        m "Ehehe~"
    else:
        m "Some of my favorite books are in there."
        m "{i}Fahrenheit 451{/i}, {i}Hard-Boiled Wonderland{/i}, {i}Nineteen Eighty-Four{/i}, and a few others."
        m "Maybe we can read them together sometime~"
    return

label mas_island_bookshelf2:
    #NOTE: this ordering is key, during winter we only use snow covered islands with clear sky
    # so Winter path needs to be first
    if mas_island_event.isWinterWeather():
        m "You know, I wouldn't mind doing some reading outside even if there is a bit of snow."
        m "Though I wouldn't venture out without a warm coat, a thick scarf, and a snug pair of gloves."
        m "I guess turning the pages might be a bit hard that way, ahaha..."
        m "But I'm sure we'll manage somehow."
        m "Isn't that right, [player]?"
    elif mas_island_event.isCloudyWeather():
        m "Reading indoors with rain just outside the window is pretty relaxing."
        m "If only I hadn't left the books outside..."
        m "I should probably bring some in here when I get the chance."
        m "I'm certain we can find other things to do meanwhile, right [player]?"
    else:
        m "Reading outdoors is a nice change of pace, you know?"
        m "I'd take a cool breeze over a stuffy library any day."
        m "Maybe I should add a table underneath the Cherry Blossom tree."
        m "It'd be nice to enjoy a cup of coffee with some snacks to go alongside my book reading."
        m "That'd be wonderful~"
    return


screen mas_islands_background:

    add mas_island_event.getBackground()

#    if morning_flag:
#        if _mas_island_window_open:
#            add "mod_assets/location/special/without_frame.png"
#        else:
#            add "mod_assets/location/special/with_frame.png"
#    else:
#        if _mas_island_window_open:
#            add "mod_assets/location/special/night_without_frame.png"
#        else:
#            add "mod_assets/location/special/night_with_frame.png"

    if _mas_island_shimeji:
        add "gui/poemgame/m_sticker_1.png" at moni_sticker_mid:
            xpos 935
            ypos 395
            zoom 0.5

screen mas_show_islands():
    style_prefix "island"
    imagemap:

        ground mas_island_event.getBackground()

#        if mas_is_raining:
#            if _mas_island_window_open:
#                ground "mod_assets/location/special/rain_without_frame.png"
#            else:
#                ground "mod_assets/location/special/rain_with_frame.png"
#        elif morning_flag:
#            if _mas_island_window_open:
#                ground "mod_assets/location/special/without_frame.png"
#            else:
#                ground "mod_assets/location/special/with_frame.png"
#        else:
#            if _mas_island_window_open:
#                ground "mod_assets/location/special/night_without_frame.png"
#            else:
#                ground "mod_assets/location/special/night_with_frame.png"


        hotspot (11, 13, 314, 270) action Return("mas_island_upsidedownisland") # island upside down
        hotspot (403, 7, 868, 158) action Return("mas_island_sky") # sky
        hotspot (699, 347, 170, 163) action Return("mas_island_glitchedmess") # glitched house
        hotspot (622, 269, 360, 78) action Return("mas_island_cherry_blossom_tree") # cherry blossom tree
        hotspot (716, 164, 205, 105) action Return("mas_island_cherry_blossom_tree") # cherry blossom tree
        hotspot (872, 444, 50, 30) action Return("mas_island_bookshelf") # bookshelf

        if _mas_island_shimeji:
            hotspot (935, 395, 30, 80) action Return("mas_island_shimeji") # Mini Moni

    if _mas_island_shimeji:
        add "gui/poemgame/m_sticker_1.png" at moni_sticker_mid:
            xpos 935
            ypos 395
            zoom 0.5

    hbox:
        yalign 0.98
        xalign 0.96
        textbutton _mas_toggle_frame_text action [ToggleVariable("_mas_island_window_open"),ToggleVariable("_mas_toggle_frame_text","Open Window", "Close Window") ]
        textbutton "Go Back" action Return(False)


# Defining a new style for buttons, because other styles look ugly

# properties for these island view buttons
style island_button is default:
    properties gui.button_properties("island_button")
    idle_background  "mod_assets/island_idle_background.png"
    hover_background "mod_assets/island_hover_background.png"
    xysize (205, None)
    ypadding 5
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style island_button_dark is default:
    properties gui.button_properties("island_button_dark")
    idle_background  "mod_assets/island_idle_background_d.png"
    hover_background "mod_assets/island_hover_background_d.png"
    xysize (205, None)
    ypadding 5
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style island_button_text is default:
    properties gui.button_text_properties("island_button")
    idle_background  "mod_assets/island_idle_background.png"
    hover_background "mod_assets/island_hover_background.png"
    font gui.default_font
    size gui.text_size
    xalign 0.5
    idle_color mas_ui.light_button_text_idle_color
    hover_color mas_ui.light_button_text_hover_color
    kerning 0.2
    outlines []

style island_button_text_dark is default:
    properties gui.button_text_properties("island_button_dark")
    idle_background  "mod_assets/island_idle_background_d.png"
    hover_background "mod_assets/island_hover_background_d.png"
    font gui.default_font
    size gui.text_size
    xalign 0.5
    idle_color mas_ui.dark_button_text_idle_color
    hover_color mas_ui.dark_button_text_hover_color
    kerning 0.2
    outlines []

# mini moni ATL
transform moni_sticker_mid:
    block:
        function randomPauseMonika
        parallel:
            sticker_move_n
        repeat
