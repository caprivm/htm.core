/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU Affero Public License for more details.
 *
 * You should have received a copy of the GNU Affero Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */

/** @file
 * Implementation of Watcher test
 */


#include <exception>
#include <sstream>
#include <string>

#include <nupic/engine/Network.hpp>
#include <nupic/engine/NuPIC.hpp>
#include <nupic/engine/Region.hpp>
#include <nupic/ntypes/Dimensions.hpp>
#include <nupic/os/Path.hpp>
#include <nupic/ntypes/ArrayBase.hpp>
#include <nupic/engine/Watcher.hpp>

#include <gtest/gtest.h>

namespace testing {
    
static bool verbose = false;
#define VERBOSE                                                                \
  if (verbose)                                                                 \
  std::cerr << "[          ] "

using namespace nupic;

TEST(WatcherTest, SampleNetwork) {
  // NOTE:  This test generates files for the subsequent two tests.
  // generate sample network   [level1] -> [level2] -> [level3]
  Network n;
  n.addRegion("level1", "TestNode", "{dim: [4,2]}");
  n.addRegion("level2", "TestNode", "");
  n.addRegion("level3", "TestNode", "");
  n.link("level1", "level2");
  n.link("level2", "level3");
  n.initialize();


  // erase any previous contents of testfile
  Directory::removeTree("TestOutputDir");
  Directory::create("TestOutputDir");

  // test creation
  Watcher w("TestOutputDir/testfile");

  // test uint32Params
  unsigned int id1 = w.watchParam("level1", "uint32Param");
  ASSERT_EQ(id1, (unsigned int)1);
  // test uint64Params
  unsigned int id2 = w.watchParam("level1", "uint64Param");
  ASSERT_EQ(id2, (unsigned int)2);
  // test int32Params
  w.watchParam("level1", "int32Param");
  // test int64Params
  w.watchParam("level1", "int64Param");
  // test real32Params
  w.watchParam("level1", "real32Param");
  // test real64Params
  w.watchParam("level1", "real64Param");
  // test stringParams
  w.watchParam("level1", "stringParam");
  // test unclonedParams
  w.watchParam("level1", "unclonedParam", 0);
  w.watchParam("level1", "unclonedParam", 1);

  // test attachToNetwork()
  w.attachToNetwork(n);

  //test two simultaneous Watchers on the same network with different files
  Watcher* w2 = new Watcher("TestOutputDir/testfile2");

  // test int64ArrayParam
  w2->watchParam("level1", "int64ArrayParam");
  // test real32ArrayParam
  w2->watchParam("level1", "real32ArrayParam");
  // test output
  w2->watchOutput("level1", "bottomUpOut");
  // test int64ArrayParam, sparse = false
  w2->watchParam("level1", "int64ArrayParam", -1, false);

  w2->attachToNetwork(n);

  // set one of the uncloned parameters to 1 instead of 0
  // n.getRegions().getByName("level1")->getNodeAtIndex(1).setParameterUInt32("unclonedParam",(UInt32)1);
  //n.run(3);
  // see if Watcher notices change in parameter values  after 3 iterations
  n.getRegions().getByName("level1")->setParameterUInt64("uint64Param", (UInt64)66);
  n.run(3);

  // test flushFile() - this should produce output
  w2->flushFile();

  // test closeFile()
  w2->closeFile();

  // test to make sure data is flushed when Watcher is deleted
  delete w2;

  // The two generated files are used in next test.
}

TEST(WatcherTest, FileTest1) {
  // test file output (Generated by the test SampleNetwork)
  ASSERT_TRUE(Path::exists("TestOutputDir/testfile"));
  std::ifstream inStream("TestOutputDir/testfile");
  std::string tempString;
  if (inStream.is_open()) {
    getline(inStream, tempString);
    ASSERT_EQ("Info: watchID, regionName, nodeType, nodeIndex, varName",
              tempString);
    getline(inStream, tempString);
    ASSERT_EQ("1, level1, TestNode, -1, uint32Param", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("2, level1, TestNode, -1, uint64Param", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("3, level1, TestNode, -1, int32Param", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("4, level1, TestNode, -1, int64Param", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("5, level1, TestNode, -1, real32Param", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("6, level1, TestNode, -1, real64Param", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("7, level1, TestNode, -1, stringParam", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("8, level1, TestNode, 0, unclonedParam", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("9, level1, TestNode, 1, unclonedParam", tempString);
    getline(inStream, tempString);
    ASSERT_EQ("Data: watchID, iteration, paramValue", tempString);

    unsigned int i = 1;
    while (!inStream.eof()) {
      std::stringstream stream;
      std::string value;
      getline(inStream, tempString);
      if (tempString.size() == 0) {
        break;
      }
      VERBOSE << tempString << "\n";

      switch (tempString.at(0)) {
      case '1':
        stream << "1, " << i << ", 33";
        break;
      case '2':
        stream << "2, " << i;
        if (i < 4) {
          stream << ", 66";
        } else {
          stream << ", 65";
        }
        break;
      case '3':
        stream << "3, " << i << ", 32";
        break;
      case '4':
        stream << "4, " << i << ", 64";
        break;
      case '5':
        stream << "5, " << i << ", 32.1";
        break;
      case '6':
        stream << "6, " << i << ", 64.1";
        break;
      case '7':
        stream << "7, " << i << ", nodespec value";
        break;
      case '8':
        stream << "8, " << i << ", ";
        break;
      case '9':
        stream << "9, " << i << ", ";
        i++;
        break;
      }

      value = stream.str();
      ASSERT_EQ(value, tempString);
    }
    inStream.close();
  }

  Path::remove("TestOutputDir/testfile");
}

TEST(WatcherTest, FileTest2) {
  //  (Generated by the test SampleNetwork)
  ASSERT_TRUE(Path::exists("TestOutputDir/testfile2"));
  std::ifstream inStream2("TestOutputDir/testfile2");
  std::string tempString;
  if (inStream2.is_open()) {
    getline(inStream2, tempString);
    ASSERT_EQ("Info: watchID, regionName, nodeType, nodeIndex, varName", tempString);
    getline(inStream2, tempString);
    ASSERT_EQ("1, level1, TestNode, -1, int64ArrayParam", tempString);
    getline(inStream2, tempString);
    ASSERT_EQ("2, level1, TestNode, -1, real32ArrayParam", tempString);
    getline(inStream2, tempString);
    ASSERT_EQ("3, level1, TestNode, -1, bottomUpOut", tempString);
    getline(inStream2, tempString);
    ASSERT_EQ("4, level1, TestNode, -1, int64ArrayParam", tempString);
    getline(inStream2, tempString);
    ASSERT_EQ("Data: watchID, iteration, paramValue", tempString);

    std::vector<std::string> expected = {
        "1, 1, 4 1 2 3",        
        "2, 1, 8 1 2 3 4 5 6 7",
        "3, 1, 8 2 3 5 6 7",    
        "4, 1, 4 0 64 128 192",
        "1, 2, 4 1 2 3",        
        "2, 2, 8 1 2 3 4 5 6 7",
        "3, 2, 8 0 2 3 4 5 6 7",
        "4, 2, 4 0 64 128 192",
        "1, 3, 4 1 2 3",
        "2, 3, 8 1 2 3 4 5 6 7",
        "3, 3, 8 0 2 3 4 5 6 7",
        "4, 3, 4 0 64 128 192"
        };
    unsigned int i = 0;
    while (!inStream2.eof()) {
      std::stringstream stream;
      std::string value;
      getline(inStream2, tempString);
      if (tempString.size() == 0) {
        break;
      }
      VERBOSE << tempString << "\n";
      EXPECT_TRUE(i < expected.size()) << "More entries than expected.";
      if (i < expected.size()) {
        EXPECT_EQ(expected[i++], tempString);
      }
    }
    ASSERT_TRUE(i == expected.size()) << "Not all entries found.";
  }
  inStream2.close();

  Path::remove("TestOutputDir/testfile2");
}
}