#!/usr/bin/env python3
import argparse
import itertools
import multiprocessing as mp
import os
import pandas as pd
from panoptes_client import Panoptes, Project, Subject, SubjectSet
import subprocess
import sys

from pydub import AudioSegment

from ChildProject.projects import ChildProject
from ChildProject.annotations import AnnotationManager

def check_dur(dur, target):
    if dur % 0.5 == 0:
        new_dur=dur
        remain=0
    else:
        closest_int=int(round(dur))
        if closest_int>=dur:
            new_dur = float(closest_int)
        else:
            new_dur = float(closest_int)+0.5
    remain = float(new_dur-dur)
    return new_dur,remain

class Chunk():
    def __init__(self, recording, onset, offset):
        self.recording = recording
        self.onset = onset
        self.offset = offset

    def getbasename(self, extension):
        return "{}_{}_{}.{}".format(
            os.path.splitext(self.recording.replace('/', '_'))[0],
            self.onset,
            self.offset,
            extension
        )

class ZooniversePipeline():
    def __init__(self, path, project_name = 'test', dataset = 'test1', zooniverse_login = '', zooniverse_pwd = '', annotation_set = 'vtc', destination = '.',
            target_speaker_type = 'CHI', sample_size = 100, chunk_length = 500, threads = 0, **kwargs):
        self.project = ChildProject(path)
        self.project_name = project_name
        self.zooniverse_login = zooniverse_login
        self.zooniverse_pwd = zooniverse_pwd
        self.annotation_set = annotation_set
        self.destination = destination
        self.target_speaker_type = target_speaker_type
        self.sample_size = int(sample_size)
        self.chunk_length = int(chunk_length)
        self.threads = int(threads)
        
        assert 1000 % self.chunk_length == 0, 'chunk_length should divide 1000'

        self.chunks = []
                

    def split_recording(self, segments):
        segments = segments.sample(self.sample_size).to_dict(orient = 'records')

        source = os.path.join(self.project.path, 'recordings', segments[0]['recording_filename'])
        audio = AudioSegment.from_wav(source)

        for segment in segments:
            onset = int(segment['segment_onset']*1000)
            offset = int(segment['segment_offset']*1000)
            difference = offset-onset

            if difference < 1000:
                tgt = 1000-difference
                onset = float(onset)-tgt/2
                offset = float(offset) + tgt/2
            else:
                new_dur,remain = check_dur((offset-onset)/1000, self.chunk_length/1000)
                onset = float(onset)-remain*1000/2
                offset = float(offset) + remain*1000/2

            onset = int(onset)
            offset = int(offset)

            intervals = range(onset, offset, self.chunk_length) 
            chunks = []

            for interval in intervals:
                chunk = Chunk(segment['recording_filename'], interval, interval + self.chunk_length)

                wav = os.path.join(self.destination, 'chunks', chunk.getbasename('wav'))
                mp3 = os.path.join(self.destination, 'chunks', chunk.getbasename('mp3'))

                if not os.path.exists(wav):
                    audio[chunk.onset:chunk.offset].export(wav, format = 'wav')

                if not os.path.exists(mp3):
                    audio[chunk.onset:chunk.offset].export(mp3, format = 'mp3')

                chunks.append(chunk)

            return chunks

    def extract_chunks(self):
        am = AnnotationManager(self.project)
        self.annotations = am.annotations
        self.annotations = self.annotations[self.annotations['set'] == self.annotation_set]
        self.segments = am.get_segments(self.annotations)
        self.segments = self.segments[self.segments['speaker_type'] == self.target_speaker_type]
        self.segments['segment_onset'] = self.segments['segment_onset'] + self.segments['time_seek']
        self.segments['segment_offset'] = self.segments['segment_offset'] + self.segments['time_seek']

        os.makedirs(os.path.join(self.destination, 'chunks'), exist_ok = True)

        segments = []
        for _recording, _segments in self.segments.groupby('recording_filename'):
            segments.append(_segments.assign(recording_filename = _recording))
        
        pool = mp.Pool(self.threads)
        self.chunks = pool.map(self.split_recording, segments)
        self.chunks = itertools.chain.from_iterable(self.chunks)
        self.chunks = pd.DataFrame([{
            'recording': c.recording,
            'onset': c.onset,
            'offset': c.offset,
            'wav': c.getbasename('wav'),
            'mp3': c.getbasename('mp3'),
            'speaker_type': self.target_speaker_type
        } for c in self.chunks])

        self.chunks.to_csv('chunks.csv')

    def upload_chunks(self):
        Panoptes.connect(username = self.zooniverse_login, password = self.zooniverse_pwd)

        zooniverse_project = Project.find(slug = self.project_name)

        self.chunks['batch'] = self.chunks.index.map(lambda x: int(x/1000))

        for batch, chunks in self.chunks.groupby('batch'):
            subject_set = SubjectSet()
            subject_set.links.project = zooniverse_project
            subject_set.display_name = "{}_batch_{}".format(args.dataset, batch)
            subject_set.save()
            subjects = []

            for chunk in chunks.to_dict(orient = 'records'):
                print("uploading chunk {} ({},{})".format(chunk['recording'], chunk['onset'], chunk['offset']))
                subject = Subject()
                subject.links.project = zooniverse_project
                subject.add_location(os.path.join(self.destination, 'chunks', chunk['mp3']))
                subject.metadata.update(chunk)
                subject.save()
                subjects.append(subject)

            subject_set.add(subjects)

    def run(self):
        self.extract_chunks()
        self.upload_chunks()


parser = argparse.ArgumentParser(description = 'split audios un chunks and upload them to zooniverse')
parser.add_argument('path', help = 'an integer for the accumulator')
parser.add_argument('--project-name', help = 'zooniverse project name', required = True)
parser.add_argument('--dataset', help = 'subject prefix', required = True)
parser.add_argument('--sample-size', help = 'how many samples per recording', required = True, type = int)
parser.add_argument('--zooniverse-login', help = 'zooniverse login', required = True)
parser.add_argument('--zooniverse-pwd', help = 'zooniverse password', required = True)
parser.add_argument('--threads', help = 'how many threads to run on', default = 0, type = int)
args = parser.parse_args()

pipeline = ZooniversePipeline(**vars(args))
pipeline.run()