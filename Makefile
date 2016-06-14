LIBDIR=/usr/lib/wb-mqtt-mhz19

.PHONY: all clean

all:
clean :

install: all
	install -d $(DESTDIR)
	install -d $(DESTDIR)/etc
	install -d $(DESTDIR)/usr/share/wb-mqtt-confed
	install -d $(DESTDIR)/usr/share/wb-mqtt-confed/schemas
	install -d $(DESTDIR)/usr
	install -d $(DESTDIR)/usr/bin
	install -d $(DESTDIR)/usr/lib
	install -d $(DESTDIR)/$(LIBDIR)

	install -m 0755 wb-mqtt-mhz19.py   $(DESTDIR)/$(LIBDIR)/

	ln -s  $(LIBDIR)/wb-mqtt-mhz19.py $(DESTDIR)/usr/bin/wb-mqtt-mhz19

	install -m 0644  wb-mqtt-mhz19.schema.json $(DESTDIR)/usr/share/wb-mqtt-confed/schemas/wb-mqtt-mhz19.schema.json
	install -m 0644  config.json $(DESTDIR)/etc/wb-mqtt-mhz19.conf









