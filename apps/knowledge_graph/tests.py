from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.users.models import Role, RoleChoices, UserProfile
from apps.libraries.models import ProgrammingLanguage, Category, Library
from apps.knowledge_graph.models import (
    KnowledgeGraphNode, KnowledgeGraphEdge, SimilarityScore, GraphSnapshot
)
from apps.knowledge_graph.services.nlp_service import NLPService
from apps.knowledge_graph.services.embedding_service import EmbeddingService
from apps.knowledge_graph.services.similarity_service import SimilarityService
from apps.knowledge_graph.services.classification_service import ClassificationService
from apps.knowledge_graph.services.relationship_service import RelationshipService
from apps.knowledge_graph.services.graph_builder_service import GraphBuilderService
from apps.knowledge_graph.services.graph_query_service import GraphQueryService

class KnowledgeGraphTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.researcher_role = Role.objects.create(role_name=RoleChoices.RESEARCHER)
        self.user = User.objects.create_user(username='graph_user', password='Password123!')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.role = self.researcher_role
        profile.save()

        self.lang = ProgrammingLanguage.objects.create(language_name='Python', slug='python')
        self.cat = Category.objects.create(category_name='JSON Parsers', slug='json-parsers')
        
        self.lib_a = Library.objects.create(
            library_name='json_std',
            official_name='json',
            current_version='3.11.0',
            programming_language=self.lang,
            category=self.cat,
            description='Standard Python JSON encoder and decoder package.'
        )
        self.lib_b = Library.objects.create(
            library_name='ujson_fast',
            official_name='ujson',
            current_version='5.7.0',
            programming_language=self.lang,
            category=self.cat,
            description='Ultra fast JSON encoder and decoder written in C for Python.'
        )

    def test_nlp_service(self):
        text = "Ultra FAST json <p>parser</p> and encoder!"
        cleaned = NLPService.clean_text(text)
        tokens = NLPService.tokenize(text)
        self.assertIn('ultra', tokens)
        self.assertIn('json', tokens)
        self.assertIn('parser', tokens)

    def test_embedding_service(self):
        emb = EmbeddingService.generate_library_embedding(self.lib_a)
        self.assertIsNotNone(emb)
        self.assertGreater(emb.dimension, 0)
        self.assertIn('json', emb.vector_json)

    def test_similarity_service(self):
        score_obj = SimilarityService.compute_library_pair_similarity(self.lib_a, self.lib_b)
        self.assertIsNotNone(score_obj)
        self.assertGreater(score_obj.cosine_similarity, 0.0)
        self.assertGreater(score_obj.composite_similarity, 0.0)
        self.assertTrue(score_obj.is_discovered)

    def test_classification_service(self):
        cat = ClassificationService.discover_category_for_library(self.lib_b)
        self.assertIsNotNone(cat)
        self.assertEqual(cat.category_name, 'JSON Parsers')

    def test_graph_builder_and_query_service(self):
        snapshot = GraphBuilderService.build_knowledge_graph()
        self.assertIsNotNone(snapshot)
        self.assertGreater(snapshot.node_count, 0)
        self.assertGreater(snapshot.edge_count, 0)

        # Query alternatives
        alts = GraphQueryService.find_alternative_libraries(self.lib_a)
        self.assertGreater(len(alts), 0)
        self.assertEqual(alts[0]['library_name'], 'ujson_fast')

        # Graph analytics summary
        analytics = GraphQueryService.get_graph_analytics_summary()
        self.assertGreater(analytics['total_nodes'], 0)
        self.assertGreater(analytics['total_edges'], 0)

    def test_knowledge_graph_views(self):
        self.client.login(username='graph_user', password='Password123!')
        
        res_exp = self.client.get(reverse('knowledge_graph:explorer'))
        self.assertEqual(res_exp.status_code, 200)

        res_sim = self.client.get(reverse('knowledge_graph:similarity_discovery'))
        self.assertEqual(res_sim.status_code, 200)

        res_rel = self.client.get(reverse('knowledge_graph:relationship_list'))
        self.assertEqual(res_rel.status_code, 200)

        res_ana = self.client.get(reverse('knowledge_graph:graph_analytics'))
        self.assertEqual(res_ana.status_code, 200)
