from decimal import Decimal
from datetime import date

from django.test import RequestFactory, TestCase

from principal.models import Contrato, ParcelaContrato
from principal.views import fcvs_contribuicao


class FcvsContribuicaoViewTests(TestCase):
    def test_zero_value_fcvs_still_appears_in_report(self):
        contrato = Contrato.objects.create(codigo='C-0001', conjunto='0001', ocorrencia='TPZ')
        ParcelaContrato.objects.create(
            contrato=contrato,
            nmens=1,
            dtvenc=date(2014, 1, 30),
            fcvs=Decimal('0.00'),
        )

        request = RequestFactory().get('/fcvs/contribuicao/', {'ano': '2014', 'periodicidade': 'mensal'})
        response = fcvs_contribuicao(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8', 'ignore')
        self.assertIn('C-0001', content)
        self.assertIn('Total mensal:', content)
        self.assertIn('R$ 0.00', content)
