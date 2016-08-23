/*!
    Copyright (C) 2016 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (GGRC, can) {
  'use strict';

  /*  GGRC.ListLoaders.ListBinding
   */
  can.Construct("GGRC.ListLoaders.ListBinding", {
  }, {
      init: function (instance, loader) {
        this.instance = instance;
        this.loader = loader;

        this.list = new can.Observe.List();
      },

      refresh_stubs: function () {
        return this.loader.refresh_stubs(this);
      },

      refresh_instances: function (force) {
        return this.loader.refresh_instances(this, force);
      },

    //  `refresh_count`
    //  - Returns a `can.compute`, which in turn returns the length of
    //    `this.list`
    //  - Attempts to do the minimal work (e.g., loading only stubs, not full
    //    instances) to return an accurate length
      refresh_count: function () {
        var self = this;
        return this.refresh_stubs().then(function () {
          return can.compute(function () {
            return self.list.attr("length");
          });
        });
      },

    //  `refresh_list`
    //  - Returns a list which will *only* ever contain fully loaded / reified
    //    instances
      refresh_list: function () {
        var loader = new GGRC.ListLoaders.ReifyingListLoader(this)
          , binding = loader.attach(this.instance)
          , self = this
          ;

        binding.name = this.name + "_instances";
        //  FIXME: `refresh_instances` should not need to be called twice, but
        //  it fixes pre-mature resolution of mapping deferreds in some cases
        return binding.refresh_instances(this).then(function () {
          return self.refresh_instances();
        });
      },

      refresh_instance: function () {
        var refresh_queue = new RefreshQueue();
        refresh_queue.enqueue(this.instance);
        return refresh_queue.trigger();
      }
  });
})(window.GGRC, window.can);
