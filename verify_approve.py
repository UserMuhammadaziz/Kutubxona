import django
django.setup()
from kitob.services import band_qilishni_tasdiqla
from kitob.models import BandQilish
from user.models import User

band = BandQilish.objects.latest('id')
xodim = User.objects.filter(rol='kutubxonachi').first()
print('Approving band ID:', band.id)
band, berish = band_qilishni_tasdiqla(band, xodim, 'Tasdiqlandi')
print('After approval: band.holati=%s, berish.id=%s' % (band.holati, berish.id if berish else None))
print('Berish oquvchi:', berish.oquvchi.fish if berish else 'None')
print('Berish kitob:', berish.kitob.nomi if berish else 'None')